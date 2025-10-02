# Dependency Notes

## The "six" Dependency Issue (RESOLVED)

### What is `six`?

`six` is a Python 2/3 compatibility library that was extremely popular during the Python 2 to Python 3 transition period (2008-2020). It provided utilities to write code that could run on both Python 2 and Python 3.

Common utilities from `six`:
- `six.with_metaclass()` - Metaclass compatibility
- `six.string_types` - String type checking across versions
- `six.iteritems()` - Dictionary iteration
- `six.moves` - Module reorganization handling

### Why Was It a Problem?

Since Python 2 reached end-of-life in January 2020, `six` is now essentially obsolete. However, many older libraries still depend on it as a legacy artifact.

In this project, the dependency chain was:
```
DiscogsRecordLabelGenerator
    └── discogs-client (v2.3.0 - DEPRECATED)
        └── six (Python 2/3 compatibility)
```

This caused issues when:
1. Users had Python installed via different package managers (Homebrew, system Python, etc.)
2. Virtual environments weren't properly activated
3. The `six` package wasn't installed in the correct Python environment

### The Solution

We replaced the **deprecated** `discogs-client` package with the actively maintained fork `python3-discogs-client`.

**Before:**
```bash
pip install discogs_client  # Old, deprecated package (requires six)
```

**After:**
```bash
pip install python3-discogs-client  # Modern fork (no six required)
```

### Why This Works

The `python3-discogs-client` library:
- ✅ Is Python 3-only (no Python 2 compatibility needed)
- ✅ Removed the `six` dependency in v2.7+ (July 2023)
- ✅ Is actively maintained by the Joalla team
- ✅ Has the same API as the original
- ✅ Uses modern Python features instead of compatibility shims

**Dependencies of `python3-discogs-client` v2.7+:**
- `requests` - HTTP library
- `oauthlib` - OAuth authentication
- `python-dateutil` - Date parsing utilities

### Migration Impact

**Code Changes Required:** NONE

The `python3-discogs-client` package provides the same `discogs_client` module namespace, so no code changes are needed:

```python
import discogs_client  # Still works!
client = discogs_client.Client('MyApp/1.0', user_token=token)
```

**Installation Changes:**
```bash
# Old requirements.txt
discogs_client

# New requirements.txt
python3-discogs-client
```

### Historical Context

1. **Original Package**: `discogs_client` by Discogs Inc.
   - Official client by Discogs.com
   - Supported Python 2 and 3
   - **Deprecated June 2020**

2. **Fork**: `python3-discogs-client` by Joalla team
   - Community-maintained continuation
   - Python 3-only
   - Active development
   - Removed `six` dependency in v2.7

### Verification

To verify you're using the correct package:

```bash
# Check which package is installed
pip list | grep discogs

# Should show:
# python3-discogs-client  2.7 (or higher)

# Should NOT show:
# discogs-client  2.3.0
```

### Related Changes

This dependency fix was implemented in commit `45b429b` as part of the `feature/cli-sync-replace-gui` branch.

**Modified Files:**
- `requirements.txt` - Changed `discogs_client` to `python3-discogs-client`
- `README.md` - Updated pip install commands and removed "six" troubleshooting note

**Impact:**
- ✅ Eliminates "No module named 'six'" errors
- ✅ Simplifies virtual environment setup
- ✅ Reduces dependency count
- ✅ Uses actively maintained library
- ✅ Future-proof (Python 3+ only)

### References

- **python3-discogs-client GitHub**: https://github.com/joalla/discogs_client
- **PyPI Package**: https://pypi.org/project/python3-discogs-client/
- **Documentation**: https://python3-discogs-client.readthedocs.io/
- **Discogs API**: https://www.discogs.com/developers/

### For Developers

If you're maintaining this project and encounter `six`-related issues:

1. **Check installed packages:**
   ```bash
   pip list | grep -E "discogs|six"
   ```

2. **If you see `discogs-client 2.3.0`, replace it:**
   ```bash
   pip uninstall discogs-client
   pip install python3-discogs-client
   ```

3. **If you still see `six` errors:**
   - Ensure you're using a virtual environment
   - Run `pip install -r requirements.txt` in the venv
   - Check that no other dependencies require `six`

4. **Note:** `python-dateutil` (a dependency of `python3-discogs-client`) still requires `six`, but this is a transitive dependency that pip handles automatically. The important fix is that `python3-discogs-client` itself doesn't directly use `six` for Python 2/3 compatibility anymore.