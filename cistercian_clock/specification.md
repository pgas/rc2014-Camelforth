# Cistercian 8×8 Clock Specification

A digital timekeeper combining the 13th-century Cistercian numeral system with an 8×8 dot matrix display.

## 1. Overview & Architectural Concept

The Cistercian numeral system encodes any four-digit integer ($0000$ to $9999$) around a central vertical stem by using axial and central reflections across four quadrants.

A 24-hour timestamp (`HH:MM`) maps directly into the glyph as a 4-digit number (e.g., `22:14` $\rightarrow$ `2214`).

### Matrix Allocation (8×8 Grid)

* **Columns 0–2 (Left Wing, 3 px wide):** Left branches of the Cistercian cipher.
* **Column 3 (Center Stem, 1 px wide):** Permanently illuminated vertical backbone.
* **Columns 4–6 (Right Wing, 3 px wide):** Right branches of the Cistercian cipher.
* **Column 7 (Status Column, 1 px wide):** Dedicated weekday indicator and Daylight Saving Time (DST) flag.

```
         COLUMNS
         0 1 2   3   4 5 6   7
  ROW 0  . . . | # | . . . | .   <- Top Branch / Outer Edge    (Monday on Col 7)
  ROW 1  . . . | # | . . . | .   <- Diagonal / Outer Verticals (Tuesday on Col 7)
  ROW 2  . . . | # | . . . | .   <- Low Branch / Inner Edge    (Wednesday on Col 7)
  ROW 3  . . . | # | . . . | .   <- Central Waist Padding      (Thursday on Col 7)
  ROW 4  . . . | # | . . . | .   <- Central Waist Padding      (Friday on Col 7)
  ROW 5  . . . | # | . . . | .   <- Low Branch / Inner Edge    (Saturday on Col 7)
  ROW 6  . . . | # | . . . | .   <- Diagonal / Outer Verticals (Sunday on Col 7)
  ROW 7  . . . | # | . . . | .   <- Bottom Branch / Outer Edge (Daylight Saving on Col 7)
         \___/   |   \___/   |
         Left   Stem Right  Day / Status
```

## 2. Quadrant & Place-Value Mapping

The clock follows historical Cistercian place-value arrangement:

| Quadrant | Rows | Columns | Value Encoded | Historical Place |
| :--- | :--- | :--- | :--- | :--- |
| **Top-Left** | Rows 0–2 | Cols 0–2 | **Minute Tens** ($0 - 5$) | Tens ($10^1$) |
| **Top-Right** | Rows 0–2 | Cols 4–6 | **Minute Units** ($0 - 9$) | Units ($10^0$) |
| **Bottom-Left** | Rows 5–7 | Cols 0–2 | **Hour Tens** ($0 - 2$) | Thousands ($10^3$) |
| **Bottom-Right** | Rows 5–7 | Cols 4–6 | **Hour Units** ($0 - 9$) | Hundreds ($10^2$) |

> **Rows 3 and 4** remain unlit in Columns 0–2 and 4–6 to preserve visual separation between the upper (minute) and lower (hour) wings.

## 3. The 3×3 Digit Primitive Set (0–9)

All digits are rendered in a $3\times3$ pixel wing attached to the stem. The reference orientation below represents the **Units (Top-Right)** quadrant, where the stem is immediately to the left:

```
       0                 1                 2                 3                 4
  S . . .           S # # #           S . . .           S # . .           S . . #
  S . . .           S . . .           S . . .           S . # .           S . # .
  S . . .           S . . .           S # # #           S . . #           S # . .
 (no marks)       (outer bar)       (inner bar)       (diagonal \)      (diagonal /)

       5                 6                 7                 8                 9
  S # # #           S . . #           S # # #           S . . #           S # # #
  S . . #           S . . #           S . . #           S . . #           S . . #
  S # . .           S . . #           S # # #           S # # #           S # # #
  (1 + 4)          (outer vertical)   (1 + 6)           (2 + 6)         (1 + 2 + 6)
```

### Symmetries Across Quadrants

* **Top-Left (Tens):** Horizontally mirrored across Column 3 ($X \rightarrow 2 - X$).
* **Bottom-Right (Hundreds):** Vertically mirrored across Rows 3–4 ($Y \rightarrow 2 - Y$).
* **Bottom-Left (Thousands):** Both horizontally and vertically mirrored.

## 4. Column 7: Day of the Week & Daylight Saving

Column 7 acts as an independent vertical indicator:

* **Rows 0–6:** **Day of the Week**
  * Row 0: Monday
  * Row 1: Tuesday
  * Row 2: Wednesday
  * Row 3: Thursday
  * Row 4: Friday
  * Row 5: Saturday
  * Row 6: Sunday
* **Row 7:** **Daylight Saving Status**
  * `OFF`: Standard Time
  * `ON`: Daylight Saving Time active

## 5. Visual Example: `22:14` (Tuesday, Daylight Saving Active)

* **Time:** `22:14`
* **Top-Left (Min Tens = 1):** Row 0 lit (outer bar).
* **Top-Right (Min Units = 4):** Diagonal lit from $(4,2)$ to $(6,0)$.
* **Bottom-Left (Hr Tens = 2):** Row 5 lit (inner bar).
* **Bottom-Right (Hr Units = 2):** Row 5 lit (inner bar).
* **Column 3 (Stem):** Permanently lit from Row 0 to Row 7.
* **Column 7 (Status):** Row 1 (Tuesday) and Row 7 (Daylight Saving active) lit.

### Pixel Matrix (`#` = Lit, `.` = Off)

```
       Col: 0 1 2   3   4 5 6   7 (Status)
    Row 0:  # # # | # | . . # | .  <- Monday
    Row 1:  . . . | # | . # . | #  <- Tuesday Active
    Row 2:  . . . | # | # . . | .  <- Wednesday
    Row 3:  . . . | # | . . . | .  <- Thursday
    Row 4:  . . . | # | . . . | .  <- Friday
    Row 5:  # # # | # | # # # | .  <- Saturday (22 Hours on glyph)
    Row 6:  . . . | # | . . . | .  <- Sunday
    Row 7:  . . . | # | . . . | #  <- Daylight Saving Active
```
