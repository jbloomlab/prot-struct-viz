# The rendered page

What a reader of the output can do with it. Nothing here needs the spec that produced it.

## The controls below the structure

The page has its own controls beneath the structure, under the viewport that holds
Mol\*'s.

**View** appears when the spec lists more than one view, and switches which is on screen.
Every view is drawn when the page loads, so switching changes only what is visible: a site
you framed stays framed, and each view brings its own caption with it. The exception is a
view with its own [`orientation`](spec.md#orientation), which deliberately moves the
camera.

**Labels** shows and hides the labels drawn on the structure. It appears only when at
least one was actually drawn: a row asking for a label on a residue the view does not
display leaves nothing to toggle, and is reported as a warning instead. Mouseover
tooltips are separate and keep working while the labels are hidden.

**Reset view** reloads the page as generated, putting the original coloring and the
current view's camera back. It is there because a representation you *add* from Mol\*'s
Components panel arrives in Mol\*'s own element coloring and cannot be colored from the
UI — see [How it works](internals.md#annotation-tables-not-baked-in-colors).

## Linking to a view

The address bar tracks whichever view is on screen, so sharing one is copying the URL:

```
https://example.org/hemagglutinin.html#view=perth-2009-to-subclade-k
```

The name after `#view=` is the view's name from the spec, lowercased with everything that
is not a letter or digit turned into a hyphen. A name the page does not have is ignored
and it opens on the first view, so an old link never lands on an error.

## Size, shading, and Mol\*'s own panels

Three spec keys decide what the page looks like when it opens:
[`viewer_height`](spec.md#top-level-keys) sets how tall the viewer box is — the width
always fills the page — [`molstar_ui`](spec.md#top-level-keys) whether Mol\*'s own
panels start open or closed, and [`style`](spec.md#top-level-keys) whether the structure
is shaded the way Mol\* shades it by default or with Mol\*'s illustrative look. Closed is
not gone: the wrench in the viewport opens them either way, which is what makes a page a
figure first and a tool second.

Mol\*'s own Quick Styles panel sets the same shading, so a reader with the panels open can
click **Default** there to see the structure the other way. **Reset view** puts the spec's
style back, along with everything else.

## Saving an image

The page has no export button of its own: Mol\*'s is better. The camera icon in the
viewport opens a panel with a **Download** button and, above it, the settings that decide
what gets downloaded — resolution, transparent background, whether the orientation axes
are drawn, and the file format.

A large export is genuinely sharper rather than a blow-up of the viewport: Mol\* re-renders
it offscreen with quality settings the live view cannot afford, so expect a few seconds and
a frozen view at the larger sizes.
[How it works](internals.md#why-a-large-export-is-sharper) has the details, including why
there is no ray tracing to turn on.
