# Codex Pet Sprite Spec

Custom pets are installed as a folder containing `pet.json` and `spritesheet.webp`.

```text
atlas: 1536 x 1872 px
grid: 8 columns x 9 rows
cell: 192 x 208 px
format: WebP with alpha
```

Rows:

| Row | State | Frames |
| --- | --- | ---: |
| 0 | `idle` | 6 |
| 1 | `running-right` | 8 |
| 2 | `running-left` | 8 |
| 3 | `waving` | 4 |
| 4 | `jumping` | 5 |
| 5 | `failed` | 8 |
| 6 | `waiting` | 6 |
| 7 | `running` | 6 |
| 8 | `review` | 6 |

Unused cells in each row must stay fully transparent.
