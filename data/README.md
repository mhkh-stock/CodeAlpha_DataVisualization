# Dataset notes

`penguins.csv` is the simplified Palmer Penguins dataset used in the prior
CodeAlpha Task 2 project. It contains 344 observations of adult Adelie,
Chinstrap, and Gentoo penguins from three islands in the Palmer Archipelago,
Antarctica.

Columns:

| Column | Meaning |
| --- | --- |
| `species` | Penguin species |
| `island` | Island where the observation was made |
| `bill_length_mm` | Bill length in millimetres |
| `bill_depth_mm` | Bill depth in millimetres |
| `flipper_length_mm` | Flipper length in millimetres |
| `body_mass_g` | Body mass in grams |
| `sex` | Recorded sex, where available |

The project deliberately retains missing values in the source CSV. The Python
script drops only the missing values needed for an individual chart and reports
the missing-value counts when it runs.

Source and credit: the data were collected and made available by Dr. Kristen
Gorman and the Palmer Station, Antarctica LTER. This simplified version is
distributed through the [palmerpenguins project](https://allisonhorst.github.io/palmerpenguins/).
