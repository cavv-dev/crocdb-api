# Crocdb API Documentation

The Crocdb API provides access to the database of ROM entries, platforms and regions. The API is hosted at `https://api.crocdb.net` and is publicly accessible.

## Response Format

All API endpoints return responses in the following JSON format:

```jsonc
{
  "info": {
    // Information about the request or error messages
  },
  "data": {
    // The actual data returned by the endpoint
  }
}
```

## Endpoints

### Search Entries

Searches for ROM entries using various filters.

- **URL**: `/search`
- **Method**: `POST`
- **Request Body**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search_key | string | No | Search term to find matching entries |
| platforms | array of strings | No | List of platform IDs to filter by |
| regions | array of strings | No | List of region IDs to filter by |
| rom_id | string | No | Filter by specific ROM ID |
| max_results | integer | No | Maximum number of results per page (default: 100, max: 100) |
| page | integer | No | Page number for pagination (default: 1) |

- **Example Request**:

```json
{
  "search_key": "mario",
  "platforms": ["snes", "n64"],
  "regions": ["us", "eu"],
  "max_results": 50,
  "page": 1
}
```

- **Response**:

```jsonc
{
  "info": {},
  "data": {
    "results": [
      {
        "slug": "mario-is-missing-snes-eu",
        "rom_id": null,
        "title": "Mario Is Missing!",
        "platform": "snes",
        "boxart_url": "https://thumbnails.libretro.com/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/Named_Boxarts/Mario%20Is%20Missing%21%20%28Europe%29.png",
        "regions": [
          "eu"
        ],
        "links": [
          {
            "name": "Mario Is Missing! (Europe)",
            "type": "Game",
            "format": "sfc",
            "url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/Mario%20Is%20Missing%21%20%28Europe%29.zip",
            "filename": "Mario Is Missing! (Europe).zip",
            "host": "Myrient",
            "size": 925491,
            "size_str": "903.8K",
            "source_url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/"
          },
          // ...
        ]
      },
      // ...
    ],
    "current_results": 50,
    "total_results": 75,
    "current_page": 1,
    "total_pages": 2
  }
}
```

### Get Entry

Retrieves a specific entry by its slug identifier.

- **URL**: `/entry`
- **Method**: `POST`
- **Request Body**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| slug | string | Yes | The unique slug identifier for the entry |

- **Example Request**:

```json
{
  "slug": "croc-legend-of-the-gobbos-ps1-us"
}
```

- **Response**:

```jsonc
{
  "info": {},
  "data": {
    "entry": {
      "slug": "croc-legend-of-the-gobbos-ps1-us",
      "rom_id": "SLUS-00530",
      "title": "Croc - Legend of the Gobbos",
      "platform": "ps1",
      "boxart_url": "https://thumbnails.libretro.com/Sony%20-%20PlayStation/Named_Boxarts/Croc%20-%20Legend%20of%20the%20Gobbos%20%28USA%29.png",
      "regions": [
        "us"
      ],
      "links": [
        {
          "name": "Croc - Legend of the Gobbos (USA)",
          "type": "Game",
          "format": "bin/cue",
          "url": "https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation/Croc%20-%20Legend%20of%20the%20Gobbos%20%28USA%29.zip",
          "filename": "Croc - Legend of the Gobbos (USA).zip",
          "host": "Myrient",
          "size": 388392550,
          "size_str": "370.4M",
          "source_url": "https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation/"
        },
        // ...
      ]
    }
  }
}
```

### Random Entry

Returns a randomly selected entry from the database.

- **URL**: `/entry/random`
- **Methods**: `POST`, `GET`
- **Request Body**: None required
- **Response**: Same format as the `/entry` endpoint

### Available Platforms

Returns a list of all available platforms in the database.

- **URL**: `/platforms`
- **Methods**: `POST`, `GET`
- **Request Body**: None required
- **Response**:

```jsonc
{
  "info": {},
  "data": {
    "platforms": {
      "nes": {
        "brand": "Nintendo",
        "name": "Nintendo Entertainment System"
      },
      "fds": {
        "brand": "Nintendo",
        "name": "Famicom Disk System"
      },
      "snes": {
        "brand": "Nintendo",
        "name": "Super Nintendo Entertainment System"
      },
      // ...
    }
  }
}
```

### Available Regions

Returns a list of all available regions in the database.

- **URL**: `/regions`
- **Methods**: `POST`, `GET`
- **Request Body**: None required
- **Response**:

```json
{
  "info": {},
  "data": {
    "regions": {
      "eu": "Europe",
      "us": "USA",
      "jp": "Japan",
      "other": "Other"
    }
  }
}
```

### Database Information

Returns general information about the database.

- **URL**: `/info`
- **Methods**: `POST`, `GET`
- **Request Body**: None required
- **Response**:

```json
{
  "info": {},
  "data": {
    "total_entries": 152241
  }
}
```

## Error Handling

If an error occurs, the API will return an appropriate HTTP status code along with an error message in the `info` object:

```json
{
  "info": {
    "error": "An unexpected error occurred"
  },
  "data": {}
}
```

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) with all origins allowed.
