# HTTP Caching

Scrag includes a lightweight HTTP caching system that improves performance for repeated runs on the same URLs by avoiding unnecessary network requests.

## Features

- **On-disk caching**: Cached responses are stored locally in JSON format
- **ETag and Last-Modified support**: Respects HTTP cache headers for efficient conditional requests
- **Configurable cache settings**: Control cache location, expiration, and enable/disable
- **Cache bypass**: Option to disable caching for specific runs
- **Cache management**: CLI commands to inspect and clear cache

## Configuration

### Default Settings

The cache is enabled by default with the following settings:

```yaml
scraping:
  cache:
    enabled: true
    max_age: 3600  # 1 hour in seconds
    directory: null  # null means use default ~/.scrag/cache
```

### Cache Directory

By default, cache files are stored in `~/.scrag/cache/`. You can customize this location:

```yaml
scraping:
  cache:
    directory: "/path/to/custom/cache"
```

### Cache Expiration

The `max_age` setting controls how long cached entries remain valid (in seconds). After this time, cached entries are considered expired and will be refetched.

## Usage

### Basic Usage

Caching works automatically when enabled. No changes to your existing commands are needed:

```bash
# First run - fetches from network and caches response
uv run scrag extract https://example.com/article

# Second run - uses cached response (much faster)
uv run scrag extract https://example.com/article
```

### Cache Bypass

Use the `--no-cache` flag to bypass caching for a specific run:

```bash
# Force fresh fetch, ignoring cache
uv run scrag extract https://example.com/article --no-cache
```

### Cache Management

#### View Cache Information

```bash
uv run scrag cache info
```

Output:
```
Cache Information:
  Directory: /Users/username/.scrag/cache
  Entries: 15
  Size: 2,456,789 bytes
```

#### Clear Cache

```bash
uv run scrag cache clear
```

## How It Works

### Cache Key Generation

Cache entries are keyed by:
- URL
- Relevant headers (User-Agent, Accept, Accept-Language)

This ensures that different user agents or content preferences get separate cache entries.

### Conditional Requests

When a cached entry exists, Scrag makes conditional HTTP requests using:
- `If-None-Match` header (ETag)
- `If-Modified-Since` header (Last-Modified)

If the server responds with `304 Not Modified`, the cached content is used without downloading the full response.

### Cache Storage

Each cache entry is stored as a JSON file containing:
- Original URL and request headers
- Response content and status code
- Response headers (including ETag, Last-Modified)
- Timestamp for expiration checking

## Performance Benefits

### Speed Improvements

- **First run**: Normal network request time
- **Subsequent runs**: Near-instant response from cache
- **Conditional requests**: Only downloads if content changed

### Bandwidth Savings

- Avoids re-downloading unchanged content
- Reduces server load through conditional requests
- Particularly beneficial for large pages or slow connections

## Troubleshooting

### Cache Not Working

1. Check if caching is enabled in configuration
2. Verify cache directory permissions
3. Use `--no-cache` to test without cache

### Stale Content

If you're seeing outdated content:

1. Clear the cache: `uv run scrag cache clear`
2. Use `--no-cache` for fresh content
3. Check cache expiration settings

### Cache Directory Issues

If you encounter permission errors:

1. Ensure the cache directory is writable
2. Change the cache directory in configuration
3. Run with appropriate permissions

## Advanced Configuration

### Per-Extractor Cache Settings

You can configure cache settings per extractor:

```yaml
pipeline:
  extractor_options:
    http:
      enable_cache: true
      cache_max_age: 7200  # 2 hours
      cache_dir: "/custom/cache/path"
```

### Disable Caching Globally

To disable caching entirely:

```yaml
scraping:
  cache:
    enabled: false
```

## Best Practices

1. **Use appropriate cache expiration**: Balance freshness vs performance
2. **Monitor cache size**: Use `cache info` to track disk usage
3. **Clear cache periodically**: Especially for development/testing
4. **Use `--no-cache` for critical updates**: When you need the latest content
5. **Configure cache directory**: Use a location with sufficient disk space
