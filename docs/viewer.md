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

**Labels** shows and hides the persistent on-structure labels. It appears only when the
CSV asked for at least one and the view could place it, and it moves all of them at once —
including the copy drawn on every symmetry mate of an assembly. Mouseover tooltips are
separate and keep working while the labels are hidden.

**Reset view** reloads the page as generated, putting the original coloring and the
current view's camera back. It is there because of one limitation: a representation you
*add* from Mol\*'s Components panel arrives in Mol\*'s default element coloring, not the
CSV's, and there is no way to color it from the UI. Tooltips and labels keep working on
it; only the color is missing. See [How it works](internals.md#annotation-tables-not-baked-in-colors) for why,
and for what the entries in the Components panel are named after.

## Linking to a view

The address bar names whichever view is on screen, so sharing one is copying the URL:

```
https://example.org/hemagglutinin.html#view=perth-2009-to-subclade-k
```

Opening that link starts on that view, framed and captioned, rather than on the first one.
Switching views in the page rewrites the fragment in place, which is why you never have to
work out the name yourself — go to the view you mean and copy what is in the bar. The
browser's Back button is unaffected: it leaves the page rather than stepping back through
the views you looked at.

The name after `view=` is the view's name from the spec, lowercased with everything that is
not a letter or digit turned into a hyphen. A name the page does not have is ignored and it
opens on the first view, so an old link never lands on an error.

A fragment is handled entirely by the browser and is never sent to the server, so this
works the same over `file://`, a local server, and GitHub Pages, with nothing to configure.
If a browser will not let a local file rewrite its own address bar, only the rewriting is
lost — following a link still works.

## Size, and Mol\*'s own panels

Two spec keys decide what the page looks like when it opens:
[`viewer_height`](spec.md#top-level-keys) sets how tall the viewer box is — the width
always fills the page — and [`molstar_ui`](spec.md#top-level-keys) whether Mol\*'s own
panels start open or closed. Closed is not gone: the wrench in the viewport opens them
either way, which is what makes a page a figure first and a tool second.

## Saving an image

The page has no export button of its own: Mol\*'s is better. The camera icon in the
viewport opens a panel with a **Download** button and, above it, the settings that decide
what gets downloaded — resolution, transparent background, whether the orientation axes
are drawn, and the file format.

The resolution presets are Viewport, HD (1280 x 720), Full HD (1920 x 1080), Ultra HD
(3840 x 2160), 8K Ultra HD (7680 x 4320), and Custom. Custom runs from 128 px up to a
limit your GPU sets, which the panel's own slider shows. Mol\* does not check the
*presets* against that limit, so on hardware at the lower end the 8K preset can fail where
a custom size of the same order will not.

A large export is genuinely sharper rather than a blow-up of the viewport: Mol\* re-renders
it offscreen with quality settings the live view cannot afford, so expect a few seconds and
a frozen view at the larger sizes.
[How it works](internals.md#why-a-large-export-is-sharper) has the details, including why
there is no ray tracing to turn on.
