"""
This module provides an API for interacting with the Crocdb SQLite database containing information about ROM entries, platforms, and regions. 
It includes functions for searching entries, retrieving specific entries, and fetching metadata about the database.
"""
import sqlite3
import os
import re
from unidecode import unidecode
from functools import wraps
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'db', 'roms.db')


def normalize_repeated_chars(text: str, char: str) -> str:
    """Replace consecutive occurrences of a character with a single instance."""
    escaped_char = re.escape(char)  # Escape special characters for regex
    return re.sub(f'{escaped_char}+', char, text).strip()


def replace_invalid_chars(title: str) -> str:
    """Replace invalid characters in a string with valid substitutes."""
    for value1, value2 in {
        '+': 'plus',
        '&': 'and',
        '™': '',
        '©': '',
        '®': ''
    }.items():
        title = title.replace(value1, f' {value2} ')
    return title


def get_valid_search_key(search_key: str) -> str:
    """Process the input search key by performing a series of transformations to ensure it is valid."""
    search_key = replace_invalid_chars(search_key)
    search_key = unidecode(search_key)
    search_key = normalize_repeated_chars(search_key, ' ')
    search_key = search_key.strip()
    return search_key


def create_db_search_key(title: str) -> str:
    """Create a search key by transforming a string using the same format used in the database"""
    title = get_valid_search_key(title)
    title = title.lower()
    title = re.sub(r"[^a-z0-9]", '', title)
    title = title.strip()
    return title


def prepare_search_key(search_key: str) -> str:
    """Make the given string safe for use in a SQL MATCH operator."""
    words = search_key.split()
    escaped_words = [word.replace('"', r'""') for word in words]
    quoted_words = [f'"{word}"' for word in escaped_words]
    return ' '.join(quoted_words)


def with_db(func):
    """Decorator that provides a read-only database connection and cursor to a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        con = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        try:
            result = func(cur, *args, **kwargs)
        finally:
            cur.close()
            con.close()
        return result
    return wrapper


def build_response(info: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build the universal response structure used in the API."""
    return {
        'info': info or {},
        'data': data or {}
    }


def handle_exception(func):
    """Decorator that handles exceptions for all API endpoints."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError:
            return build_response({'error': "Database operation failed"})
        except sqlite3.DatabaseError:
            return build_response({'error': "A database error occurred"})
        except ValueError:
            return build_response({'error': "Invalid input provided"})
        except Exception:
            return build_response({'error': "An unexpected error occurred"})
    return wrapper


@with_db
@handle_exception
def get_search(
    cur: sqlite3.Cursor,
    search_key: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    rom_id: Optional[str] = None,  # Added rom_id parameter
    max_results: int = 100,
    page: int = 1
) -> Dict[str, Any]:
    """Perform a search using given filters."""
    platforms = platforms or []
    regions = regions or []
    # Ensure max_results is between 1 and 100
    max_results = max(1, min(max_results, 100))
    page = max(1, page)  # Ensure page is at least 1

    base_query = """
    SELECT DISTINCT e.slug, e.rom_id, e.title, e.platform, e.boxart_url
    FROM entries e
    """
    where_clauses = []
    params = []

    if search_key:
        prepared_search_key = prepare_search_key(search_key)
        base_query += " JOIN entries_fts fts ON fts.rowid = e.rowid "
        where_clauses.append("fts.search_key MATCH ?")
        params.append(prepared_search_key)

    if platforms:
        placeholders = ','.join(['?' for _ in platforms])
        where_clauses.append(f"e.platform IN ({placeholders})")
        params.extend(platforms)

    if regions:
        base_query += """
        LEFT JOIN regions_entries re ON re.entry = e.slug
        """
        where_clauses.append("(re.region IN ({}) OR re.region IS NULL)".format(
            ','.join(['?' for _ in regions])
        ))
        params.extend(regions)

    if rom_id:
        where_clauses.append("e.rom_id = ?")
        params.append(rom_id)

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    count_query = f"SELECT COUNT(*) FROM ({base_query})"
    cur.execute(count_query, params)
    total_results = cur.fetchone()[0]

    total_pages = (total_results + max_results -
                   1) // max_results if max_results > 0 else 1
    page = min(page, total_pages)
    offset = (page - 1) * max_results

    if search_key:
        db_search_key = create_db_search_key(search_key)
        final_query = base_query + \
            f" ORDER BY (fts.search_key LIKE ? || '%') DESC LIMIT ? OFFSET ?"
        params_with_pagination = params + [db_search_key, max_results, offset]
    else:
        final_query = base_query + " LIMIT ? OFFSET ?"
        params_with_pagination = params + [max_results, offset]

    cur.execute(final_query, params_with_pagination)
    results = []

    for row in cur.fetchall():
        entry = dict(row)

        cur.execute("""
            SELECT region FROM regions_entries
            WHERE entry = ?
        """, (entry['slug'],))
        entry['regions'] = [region[0] for region in cur.fetchall()]

        cur.execute("""
            SELECT name, type, format, url, filename, host, size, size_str, source_url
            FROM links
            WHERE entry = ?
        """, (entry['slug'],))
        entry['links'] = [dict(link_row) for link_row in cur.fetchall()]

        results.append(entry)

    return build_response(
        {},
        {
            'results': results,
            'current_results': len(results),
            'total_results': total_results,
            'current_page': page,
            'total_pages': total_pages
        }
    )


@with_db
@handle_exception
def get_entry(cur: sqlite3.Cursor, slug: Optional[str] = None, random: bool = False) -> Dict[str, Any]:
    """Select an entry directly by its slug or get a random entry."""
    if random:
        cur.execute("""
            SELECT slug, rom_id, title, platform, boxart_url
            FROM entries
            ORDER BY RANDOM()
            LIMIT 1
        """)
        row = cur.fetchone()
        if not row:
            return build_response()
        entry = dict(row)
    else:
        if not slug:
            return build_response({'error': 'Slug is required'})
        cur.execute("""
            SELECT slug, rom_id, title, platform, boxart_url
            FROM entries
            WHERE slug = ?
        """, (slug,))
        row = cur.fetchone()
        if not row:
            return build_response({'error': 'Entry not found'})
        entry = dict(row)

    cur.execute("""
        SELECT region FROM regions_entries
        WHERE entry = ?
    """, (entry['slug'],))
    entry['regions'] = [region[0] for region in cur.fetchall()]

    cur.execute("""
        SELECT name, type, format, url, filename, host, size, size_str, source_url
        FROM links
        WHERE entry = ?
    """, (entry['slug'],))
    entry['links'] = [dict(link_row) for link_row in cur.fetchall()]

    return build_response({}, {'entry': entry})


@with_db
@handle_exception
def get_platforms(cur: sqlite3.Cursor) -> Dict[str, Any]:
    """Get the available platforms in the database."""
    cur.execute("""
        SELECT id, brand, name
        FROM platforms
    """)
    platforms = {id: {'brand': brand, 'name': name}
                 for id, brand, name in cur.fetchall()}
    return build_response({}, {'platforms': platforms})


@with_db
@handle_exception
def get_regions(cur: sqlite3.Cursor) -> Dict[str, Any]:
    """Get the available regions in the database."""
    cur.execute("""
        SELECT id, name
        FROM regions
    """)
    regions = {id: name for id, name in cur.fetchall()}
    return build_response({}, {'regions': regions})


@with_db
@handle_exception
def get_info(cur: sqlite3.Cursor) -> Dict[str, Any]:
    """Get information on the current state of the database."""
    cur.execute("SELECT COUNT(*) FROM entries")
    total_entries = cur.fetchone()[0]
    return build_response({}, {'total_entries': total_entries})
