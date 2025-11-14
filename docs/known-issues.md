# Engineering Roadmap & Planned Improvements

This document lists improvements I plan to add as the project grows. Everything works well for personal use and small workloads right now; the items below are focused on making the service more scalable, secure, and reliable over time.

---

## Reliability & Robustness

### 1. Automatic Retries with Backoff for Background Tasks

**Goal:** Make cleanup/transcription/Notion sync more resilient to short outages (Ollama restarting, network hiccups, etc.).

**Current behavior**

Background tasks treat any exception as a permanent failure:

```python
# app/routes/cleanup.py
except Exception as e:
    await db_service.update_cleaned_entry_processing(
        db=db,
        cleaned_entry_id=cleaned_entry_id,
        cleanup_status=CleanupStatus.FAILED,
        error_message=str(e),
    )
```

If Ollama is briefly down, the entry is just marked as `FAILED` and never retried.

**Plan**

Add a small retry wrapper with exponential backoff and a simple distinction between “temporary” and “permanent” errors:

```python
MAX_RETRIES = 3
RETRY_DELAYS = [5, 10, 20]  # seconds

async def process_with_retry(task_func, entry_id):
    """Retry transient errors with simple exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            return await task_func()
        except TemporaryError:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])
                continue
            mark_as_failed(entry_id)
        except PermanentError:
            mark_as_failed(entry_id)
            break
```

Use this pattern for:

- LLM cleanup jobs  
- Transcription jobs
- Notion sync

---

### 2. Streaming Uploads Instead of Reading Files into Memory

**Goal:** Keep memory usage stable even with large audio uploads and concurrent users.

**Current behavior**

Validation reads the entire file into memory:

```python
# app/utils/validators.py
contents = await file.read()
file_size = len(contents)
await file.seek(0)
```

A few 80–100 MB uploads in parallel can chew up a lot of RAM.

**Plan**

Validate and save files in streaming fashion (fixed chunk size), and enforce the size limit while streaming:

```python
async def save_file_streaming(file: UploadFile, destination: Path, max_size: int) -> int:
    """Stream file to disk in chunks while tracking total size."""
    total_size = 0
    chunk_size = 1024 * 1024  # 1MB

    async with aiofiles.open(destination, "wb") as f:
        while chunk := await file.read(chunk_size):
            total_size += len(chunk)
            if total_size > max_size:
                await f.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(413, "File too large")
            await f.write(chunk)

    return total_size
```

This keeps memory usage low and still gives the final file size for logging / DB.

---

## Security Hardening

### 3. Validate File Type by Content, Not Just Headers

**Goal:** Make file validation safe for untrusted users by checking the actual file bytes, not just what the client claims.

**Current behavior**

Validation trusts `Content-Type` and extension:

```python
if file.content_type not in ALLOWED_CONTENT_TYPES:
    raise HTTPException(400, "Invalid content type")
```

A user can rename `virus.exe` to `song.mp3` and spoof the MIME type.

**Plan**

Use “magic number” / content sniffing to verify the real MIME type:

```python
import magic

async def validate_file_type(file: UploadFile) -> str:
    """Check MIME type based on file content."""
    header = await file.read(2048)
    await file.seek(0)

    detected = magic.from_buffer(header, mime=True)
    allowed = {"audio/mpeg", "audio/mp4", "audio/x-m4a"}

    if detected not in allowed:
        raise HTTPException(400, f"Invalid file type: {detected}")

    return detected
```

For personal use this is less critical; for public use it becomes important.

---

## Performance & Data Integrity

### 4. Add Composite Indexes for Common Queries

**Goal:** Keep queries fast as the number of entries grows.

**Current situation**

- Already have useful indexes (e.g. `(entry_id, is_primary)` on transcriptions).
- Some obvious composite indexes are missing, such as:
  - `(user_id, created_at)` on `voice_entries`
  - `(user_id, status)` on `notion_syncs`

**Plan**

Add composite indexes via Alembic migrations where needed (e.g. “all entries for user X ordered by newest first”, “all Notion syncs by user + status”).

---

### 5. Enforce “Only One Primary Transcription per Entry” in the DB

**Goal:** Guarantee at the database level that an entry never has two primary transcriptions.

**Current behavior**

The app code handles this in two steps:

```python
# Pseudo-code
await db.execute(
    update(Transcription)
    .where(Transcription.entry_id == entry_id)
    .values(is_primary=False)
)

transcription.is_primary = True
```

This works in normal use, but there’s no constraint stopping a bug or manual change from creating two primaries.

**Plan**

1. Make the update atomic in a single query:

```python
from sqlalchemy import case

await db.execute(
    update(Transcription)
    .where(Transcription.entry_id == entry_id)
    .values(
        is_primary=case(
            (Transcription.id == target_id, True),
            else_=False,
        )
    )
)
```

2. Add a partial unique index:

```python
op.create_index(
    "uq_one_primary_per_entry",
    "transcriptions",
    ["entry_id"],
    unique=True,
    postgresql_where=sa.text("is_primary = true"),
    schema="journal",
)
```

That gives both atomic behavior and a hard safety net in the DB.

---

### 6. Add Pagination to List Endpoints

**Goal:** Avoid huge responses and slow queries when there are many transcriptions/cleaned entries.

**Current behavior**

Some list endpoints return everything at once (no `limit` / `offset`). This is fine today (small numbers) but doesn’t scale.

**Plan**

Use simple pagination params with safe defaults:

```python
@router.get("/entries/{entry_id}/transcriptions")
async def list_transcriptions(
    entry_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    transcriptions = await db_service.get_transcriptions_for_entry(
        db, entry_id, limit=limit, offset=offset
    )
    total = await db_service.count_transcriptions(db, entry_id)
    return {"transcriptions": transcriptions, "total": total, "limit": limit, "offset": offset}
```

Same pattern can be reused for other endpoints.

---

## Operations & Runtime Behavior

### 7. Graceful Shutdown for Background Work

**Goal:** Let in-flight background tasks finish (or at least fail cleanly) on deploy/shutdown.

**Current behavior**

On shutdown, FastAPI just drops the reference to services in `lifespan`. Background tasks can be killed mid-process, leaving entries stuck in `processing`.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    app.state.transcription_service = None
```

**Plan**

Track background tasks and add a simple graceful shutdown handler with a timeout:

```python
background_tasks: set[asyncio.Task] = set()

def track_task(task: asyncio.Task) -> None:
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

async def shutdown_tasks(timeout: float = 30.0) -> None:
    tasks = [t for t in background_tasks if not t.done()]
    for t in tasks:
        t.cancel()
    if tasks:
        await asyncio.wait(tasks, timeout=timeout)
```

Wire this into the lifespan or event handlers so that on SIGTERM/SIGINT the app waits briefly for tasks to finish before exiting.

---

### 8. Finish the Notion Sync Retry

**Goal:** Use the existing retry fields to actually retry failed Notion syncs instead of just marking them as `RETRYING`.

**Current behavior**

On error, the code updates `retry_count` and sets status to `RETRYING` but doesn’t actually trigger a retry:

```python
# app/routes/notion.py (simplified)
except Exception as e:
    new_retry_count = sync_record.retry_count + 1
    should_retry = new_retry_count < settings.NOTION_MAX_RETRIES

    await db_service.update_notion_sync_status(
        db=db,
        sync_id=sync_id,
        status=SyncStatus.RETRYING if should_retry else SyncStatus.FAILED,
    )
```

So the state is tracked, but nothing ever picks these records up again.

**Plan**

Add a small background job that periodically scans for retryable syncs and re-runs them with backoff:

```python
async def retry_failed_notion_syncs():
    """Periodically retry Notion syncs in RETRYING state."""
    async with get_session() as db:
        result = await db.execute(
            select(NotionSync)
            .where(NotionSync.status == SyncStatus.RETRYING)
            .where(NotionSync.retry_count < settings.NOTION_MAX_RETRIES)
        )

        for sync in result.scalars():
            # basic backoff logic based on retry_count + timestamps
            if ready_to_retry(sync):
                await run_single_notion_sync(db, sync)
```

This can run on a simple loop (e.g. every few minutes) or later be moved to a proper job runner / scheduler if needed.
