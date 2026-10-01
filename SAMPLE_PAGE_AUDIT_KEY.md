# Sample Inaccessible Webpage - Accessibility Audit Key

This document details all **17 deliberate accessibility barriers** built into [sample_inaccessible_page.html](file:///c:/Users/racha/OneDrive/Desktop/SEM%20III/patchly/sample_inaccessible_page.html) for testing and verifying the **Patchly** scanner.

---

## Summary of Intentional Violations

| ID | Issue Category | WCAG 2.1 Criterion | Element Location | Failure Reason | Recommended Quick Fix |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | **Keyboard / Focus** | 2.4.7 Focus Visible (AA) | Global CSS: `*:focus` | `outline: none !important;` suppresses visible keyboard focus indicator entirely. | Replace with accessible outline: `outline: 2px solid #4f46e5; outline-offset: 2px;` |
| **02** | **Color Contrast** | 1.4.3 Contrast (Minimum) (AA) | Header `<a class="nav-link">` | Text color `#94a3b8` on white `#ffffff` has ratio **~2.4:1** (Threshold is 4.5:1). | Change text color to `#475569` or darker (passes with 5.5:1). |
| **03** | **Keyboard / Semantics** | 2.1.1 Keyboard (A), 4.1.2 Name, Role, Value (A) | Header `<div class="fake-btn-cta">` | `div` with `onclick` but no `role="button"`, no `tabindex="0"`, no keyboard Enter/Space event handlers. | Convert to native `<button type="button" class="btn-cta">` or add `role="button"` and `tabindex="0"`. |
| **04** | **Structure / Headings** | 1.3.1 Info and Relationships (A), 2.4.6 Headings | Hero Section `<h4>` | Skipped heading hierarchy: `<h1>` followed immediately by `<h4>`, skipping `<h2>` and `<h3>`. | Change `<h4>` to `<h2>` or semantically appropriate sub-heading. |
| **05** | **Color Contrast** | 1.4.3 Contrast (Minimum) (AA) | Hero `<p class="hero-subtext">` | Light grey text `#a1a1aa` on light grey background `#f8fafc` has ratio **~2.1:1**. | Darken text color to `#4b5563` or `#374151` (> 6:1 ratio). |
| **06** | **Link Context** | 2.4.4 Link Purpose (In Context) (A) | Hero `<a class="non-descriptive-link">` | Anchor text says `"click here"`. Out of context, screen reader users cannot know the destination. | Update link text to: `"review our benchmark studies"`. |
| **07** | **Keyboard / Tab Order** | 2.4.3 Focus Order (A) | Hero `<a class="btn-secondary" tabindex="5">` | Positive `tabindex="5"` hijacks the natural DOM tab order, jumping focus ahead unnaturally. | Remove `tabindex="5"` or use `tabindex="0"` to respect native DOM order. |
| **08** | **Video Captions** | 1.2.2 Captions (Prerecorded) (A) | Video Section `<video>` | Video tag lacks any `<track kind="captions">` or `<track kind="subtitles">`. Deaf/HoH users cannot access speech. | Add `<track src="captions.vtt" kind="captions" srclang="en" label="English">`. |
| **09** | **Color Contrast** | 1.4.3 Contrast (Minimum) (AA) | Feature Card `<span class="badge-yellow">` | Amber/Yellow text `#f59e0b` on white `#ffffff` has ratio **~1.4:1** (severe readability failure). | Change text to darker amber `#92400e` or use dark background with light text. |
| **10** | **Form Accessibility** | 1.3.1 Info and Relationships (A), 4.1.2 Name | Form `<input type="text" id="fullname">` | Input has `placeholder` but **no `<label for="fullname">`** and no `aria-label`. | Add `<label for="fullname">Full Name</label>` before the input. |
| **11** | **Color Contrast** | 1.4.3 Contrast (Minimum) (AA) | Footer `<p class="footer-muted">` | Dark slate `#334155` on dark navy `#0f172a` has ratio **~2.1:1**. | Lighten to `#94a3b8` or `#cbd5e1` (contrast > 4.5:1). |
| **12** | **Icon / Non-Text** | 1.1.1 Non-text Content (A) | Header `<svg>` brand icon | SVG lacks `aria-hidden="true"` or `<title>` tag / `aria-label`. | Add `aria-hidden="true"` if decorative or `<title>` if informative. |
| **13** | **Image Alt Text** | 1.1.1 Non-text Content (A) | Hero 1st `<img>` (Dashboard mock) | Completely missing `alt` attribute. Screen readers announce the long image file URL. | Add descriptive `alt="ApexFlow team collaboration dashboard overview"`. |
| **14** | **Image Alt Text** | 1.1.1 Non-text Content (A) | Hero 2nd `<img>` (Analytics) | Junk alt text: `alt="image.png"`. Provides no meaningful content description. | Replace with meaningful description: `alt="Sprint burndown and velocity chart"`. |
| **15** | **Color Contrast** | 1.4.3 Contrast (Minimum) (AA) | Feature Card 2 Subtitle | Faint text `#cbd5e1` on white card `#ffffff` has contrast **~1.3:1**. | Darken to `#475569` or darker. |
| **16** | **Keyboard / Semantics** | 2.1.1 Keyboard (A) | Feature Card 3 `<span onclick="...">` | Clickable `span` acting as a hyperlink without `href`, `role="link"`, or keyboard focusability. | Replace with native `<a href="#integrations">Browse 50+ integrations &rarr;</a>`. |
| **17** | **Form Accessibility** | 1.3.1 Info and Relationships (A), 4.1.2 Name | Form `<input type="email" id="useremail">` | Missing associated `<label for="useremail">` or `aria-label`. | Add `<label for="useremail">Work Email</label>`. |

---

## How to Test This Page
1. **Open in Browser**: Open `sample_inaccessible_page.html` in Chrome, Firefox, or Edge.
2. **Keyboard-Only Test**: Try pressing `Tab` to navigate through the entire page:
   - Notice you cannot see where the focus indicator is (Violation 01).
   - Notice you can't reach or activate the "Get Started" button (Violation 03).
   - Notice the "Book a Demo" button is focused out-of-order due to `tabindex="5"` (Violation 07).
3. **Screen Reader Test**: Turn on NVDA, JAWS, or Windows Narrator (`Win + Ctrl + Enter`):
   - Listen to the images being read as filenames or `image.png` (Violations 13, 14).
   - Try navigating to form fields and notice missing label announcements (Violations 10, 17).
4. **Color Contrast Analyzer**: Sample the text colors in DevTools or axe DevTools to observe contrast ratios below 4.5:1.
