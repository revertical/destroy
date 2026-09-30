"""15 - DESTROY a slide (the chaotic way).

Turns the target slide into visual garbage, phase by phase, and then
deletes it - clearing it off the deck completely.

The "destroy system" does, in order:
  1. SPAM   - random letter garbage strewn across the slide
  2. CRUMBLE - rotate + move every element, randomise fonts, sizes,
              bold/italic/underline, text colors, shape fills, and the
              slide background itself, in two waves
  3. SCRIBBLE - draw colored scribbles (curved lines), then copy-paste
              the whole scribble blob several times in new colors
  4. MELTDOWN - dark background, final scramble
  5. DELETE

Between every phase it waits 5-10 s, so quota isn't burned in one blast
and there's time to enjoy the show / see each phase in the editor.

SAFETY: you type the presentation + slide ids yourself, the script shows
you what it will destroy, and it guards protected slides: if the slide
title contains "[DON'T DELETE]" it demands a full typed-out phrase, and
slides that mention "welcome" or "rules" need an explicit DESTROY anyway.

Run:  python 15_destroy_slide.py
"""

import math
import random
import re
import time
from uuid import uuid4

from auth import get_slides_service

# Random characters for the text spam.
SPAM_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?$%#&*+"

FONTS = [
    "Arial", "Comic Sans MS", "Courier New", "Georgia", "Impact",
    "Tahoma", "Trebuchet MS", "Verdana", "Times New Roman", "Google Sans",
    "Ubuntu"
]


def pt(magnitude):
    return {"magnitude": magnitude, "unit": "PT"}


def rnd_color():
    return {"red": random.random(), "green": random.random(), "blue": random.random()}


def rnd_text(max_len=60):
    return "".join(random.choices(SPAM_CHARS, k=random.randint(12, max_len)))


def rnd_bool():
    return random.random() < 0.5


def rnd_transform(element=None):
    """Random position + rotation matrix (absolute, in PT).

    The API only lets videos and tables be TRANSLATED - rotation/shear
    isn't supported for them - so those get a plain random move instead
    of a full rotate (which would be rejected).
    """
    if element is not None and (element.get("video") is not None
                                or element.get("table") is not None):
        return {
            "scaleX": 1,
            "scaleY": 1,
            "shearX": 0,
            "shearY": 0,
            "translateX": random.uniform(-30, 950),
            "translateY": random.uniform(-30, 530),
            "unit": "PT",
        }

    angle = random.uniform(-0.7, 0.7)            # radians (about 40 deg max)
    scale = random.uniform(0.7, 1.3)
    return {
        "scaleX": math.cos(angle) * scale,
        "scaleY": math.cos(angle) * scale,
        "shearX": -math.sin(angle) * scale,
        "shearY": math.sin(angle) * scale,
        "translateX": random.uniform(-30, 950),
        "translateY": random.uniform(-30, 530),
        "unit": "PT",
    }


def get_slide(service, presentation_id, slide_id):
    presentation = (
        service.presentations().get(presentationId=presentation_id).execute()
    )
    for slide in presentation["slides"]:
        if slide["objectId"] == slide_id:
            return slide
    return None


def slide_text(slide):
    """Concatenate every shape's text on the slide."""
    parts = []
    for element in slide.get("pageElements", []):
        text = element.get("shape", {}).get("text") or {}
        parts.extend(
            te.get("textRun", {}).get("content", "")
            for te in text.get("textElements", [])
        )
    return "".join(parts)


def confirm_target(presentation_id, slide_id):
    """Ask for ids, list slides, print what will be destroyed, confirm."""
    service = get_slides_service()

    # List slides so the user can pick the right one.
    presentation = service.presentations().get(presentationId=presentation_id).execute()
    print("Slides in deck:")
    for i, slide in enumerate(presentation["slides"]):
        snippet = slide_text(slide).replace("\n", " ")[:60]
        print(f"  [{i}] {slide['objectId']}  -> {snippet!r}")

    slide = get_slide(service, presentation_id, slide_id)
    if slide is None:
        raise SystemExit(f"Slide {slide_id!r} not found in {presentation_id!r}.")

    print(f"\nTARGET: slide {slide['objectId']!r}")
    print("This slide WILL BE VANDALISED AND DELETED. Not undoable.")

    content = slide_text(slide).lower()

    # Strongest gate: the slide title is marked [DON'T DELETE]. Requires
    # typing out a full sentence, not just a short word.
    if "[don't delete]" in content:
        phrase = (
            "I UNDERSTAND THIS SLIDE IS MARKED [DON'T DELETE] "
            "AND I STILL CHOOSE TO DESTROY IT"
        )
        print("\n!!! THIS SLIDE IS PROTECTED - its title contains [DON'T DELETE] !!!")
        print("This marker usually means an admin wants the slide kept.")
        print("Destroying it removes the sign AND the slide permanently.")
        print()
        print(f'To continue, type this exact phrase:\n  "{phrase}"')
        answer = input("> ").strip().upper()
        if answer != phrase:
            raise SystemExit("Aborted - [DON'T DELETE] slide left alone.")

    elif re.search(r"\b(rule|rules|welcome)\b", content):
        print("WARNING: this slide mentions rules/welcome. It looks like a protected slide.")
        answer = input('Type DESTROY to confirm anyway: ')
        if answer.strip() != "DESTROY":
            raise SystemExit("Aborted - protected slide left alone.")
    else:
        answer = input('Type DESTROY to confirm: ')
        if answer.strip() != "DESTROY":
            raise SystemExit("Aborted.")

    return slide


# ---------------------------------------------------------------- phases

def phase_spam(service, presentation_id, slide_id):
    """Throw random-letters text boxes all over the slide."""
    requests = []
    for i in range(9):
        box_id = f"spam_{uuid4().hex[:8]}"
        x, y = random.uniform(-20, 900), random.uniform(-10, 500)
        requests.append(
            {
                "createShape": {
                    "objectId": box_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {"width": pt(random.uniform(80, 260)),
                                 "height": pt(random.uniform(40, 140))},
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "shearX": random.uniform(-0.3, 0.3),
                            "shearY": random.uniform(-0.3, 0.3),
                            "translateX": x,
                            "translateY": y,
                            "unit": "PT",
                        },
                    },
                }
            }
        )
        requests.append(
            {"insertText": {"objectId": box_id, "insertionIndex": 0,
                            "text": rnd_text(random.randint(15, 70))}}
        )
        requests.append(
            {
                "updateTextStyle": {
                    "objectId": box_id,
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontFamily": random.choice(FONTS),
                        "fontSize": pt(random.uniform(10, 72)),
                        "bold": rnd_bool(),
                        "italic": rnd_bool(),
                        "underline": rnd_bool(),
                        "foregroundColor": {"opaqueColor": {"rgbColor": rnd_color()}},
                    },
                    "fields": "fontFamily,fontSize,bold,italic,underline,foregroundColor",
                }
            }
        )
    service.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": requests}
    ).execute()
    print("  spam: random letters everywhere")


def phase_crumble(service, presentation_id, slide_id, background_too):
    """Rotate/move everything; randomise text style, fills, background."""
    requests = []
    slide = get_slide(service, presentation_id, slide_id)

    for element in slide.get("pageElements", []):
        element_id = element["objectId"]

        # 1. every element gets thrown around + rotated
        requests.append(
            {
                "updatePageElementTransform": {
                    "objectId": element_id,
                    "applyMode": "ABSOLUTE",
                    "transform": rnd_transform(element),
                }
            }
        )

        # 2. shapes with text get random typography
        text = element.get("shape", {}).get("text")
        if text is not None:
            requests.append(
                {
                    "updateTextStyle": {
                        "objectId": element_id,
                        "textRange": {"type": "ALL"},
                        "style": {
                            "fontFamily": random.choice(FONTS),
                            "fontSize": pt(random.uniform(8, 120)),
                            "bold": rnd_bool(),
                            "italic": rnd_bool(),
                            "underline": rnd_bool(),
                            "foregroundColor": {"opaqueColor": {"rgbColor": rnd_color()}},
                        },
                        "fields": "fontFamily,fontSize,bold,italic,underline,foregroundColor",
                    }
                }
            )

        # 3. plain shapes get a random paint job
        if element.get("shape") is not None:
            requests.append(
                {
                    "updateShapeProperties": {
                        "objectId": element_id,
                        "shapeProperties": {
                            "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": rnd_color()}}}
                        },
                        "fields": "shapeBackgroundFill.solidFill.color",
                    }
                }
            )

    # 4. whole slide background gets recoloured too
    if background_too:
        requests.append(
            {
                "updatePageProperties": {
                    "objectId": slide_id,
                    "pageProperties": {
                        "pageBackgroundFill": {"solidFill": {"color": {"rgbColor": rnd_color()}}}
                    },
                    "fields": "pageBackgroundFill.solidFill.color",
                }
            }
        )

    service.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": requests}
    ).execute()
    print(f"  crumble: elements rotated/recoloured ({'with' if background_too else 'no'} bg change)")


def build_scribble_requests(slide_id):
    """Draw a 'scribble' made of colored CURVED lines (polyline isn't a
    thing in the Slides API, so the alternative is grouped curved lines).
    Returns the base line ids and the group id."""
    line_ids = [f"sb_{uuid4().hex[:8]}" for _ in range(7)]
    cx = random.uniform(200, 700)
    cy = random.uniform(100, 400)
    requests = []
    for line_id in line_ids:
        requests.append(
            {
                "createLine": {
                    "objectId": line_id,
                    "category": "CURVED",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": pt(random.uniform(60, 160)),
                            "height": pt(random.uniform(30, 80)),
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "shearX": 0,
                            "shearY": 0,
                            "translateX": cx + random.uniform(-30, 30),
                            "translateY": cy + random.uniform(-30, 30),
                            "unit": "PT",
                        },
                    },
                }
            }
        )
        requests.append(
            {
                "updateLineProperties": {
                    "objectId": line_id,
                    "lineProperties": {
                        "lineFill": {"solidFill": {"color": {"rgbColor": rnd_color()}}},
                        "weight": pt(random.uniform(1.5, 5)),
                    },
                    "fields": "lineFill,weight",
                }
            }
        )
    return line_ids, requests


def phase_scribble(service, presentation_id, slide_id):
    """Create one multicolored 'scribble' blob, group it, then duplicate
    the blob several times - each copy recoloured - i.e. copy-paste that
    many times, like a kid with a crayon."""
    line_ids, requests = build_scribble_requests(slide_id)
    group_id = f"scribble_{uuid4().hex[:8]}"
    requests.append(
        {"groupObjects": {"groupObjectId": group_id, "childrenObjectIds": line_ids}}
    )
    service.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": requests}
    ).execute()

    # DupObject into many colored scribble copies.
    for copy_index in range(6):
        child_map = {}
        new_line_ids = []
        for old_id in line_ids:
            new_id = f"sb_{uuid4().hex[:8]}"
            child_map[old_id] = new_id
            new_line_ids.append(new_id)

        copy_requests = [
            {"duplicateObject": {"objectId": group_id, "objectIds": child_map}},
            {"updatePageElementTransform": {
                "objectId": group_id,
                "applyMode": "ABSOLUTE",
                "transform": rnd_transform(),
            }},
        ]
        # Recolour each copied line of this copied blob.
        for new_id in new_line_ids:
            copy_requests.append(
                {
                    "updateLineProperties": {
                        "objectId": new_id,
                        "lineProperties": {
                            "lineFill": {"solidFill": {"color": {"rgbColor": rnd_color()}}},
                            "weight": pt(random.uniform(1.5, 6)),
                        },
                        "fields": "lineFill,weight",
                    }
                }
            )
        service.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": copy_requests}
        ).execute()
        print(f"  scribble copy {copy_index + 1}/6 spawned + recoloured")


def phase_meltdown(service, presentation_id, slide_id):
    """Dark background, one last scramble."""
    requests = [
        {
            "updatePageProperties": {
                "objectId": slide_id,
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {"color": {"rgbColor": {"red": 0.1, "green": 0.0, "blue": 0.0}}}
                    }
                },
                "fields": "pageBackgroundFill.solidFill.color",
            }
        }
    ]
    slide = get_slide(service, presentation_id, slide_id)
    for element in slide.get("pageElements", []):
        requests.append(
            {
                "updatePageElementTransform": {
                    "objectId": element["objectId"],
                    "applyMode": "ABSOLUTE",
                    "transform": rnd_transform(element),
                }
            }
        )
    service.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": requests}
    ).execute()
    print("  meltdown: dark bg + final scramble")


def delete_slide(service, presentation_id, slide_id):
    service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": [{"deleteObject": {"objectId": slide_id}}]},
    ).execute()
    print(f"  SLIDE {slide_id} DELETED. It is gone. :)")


def pause():
    seconds = random.uniform(5, 10)
    print(f"  ...pausing {seconds:.1f}s (quota/breathing room)")
    time.sleep(seconds)


# ---------------------------------------------------------------- main

def main():
    presentation_id = input("Presentation ID (from the URL, required): ").strip()
    if not presentation_id:
        raise SystemExit("No presentation ID given. Aborting.")

    service = get_slides_service()
    presentation = service.presentations().get(presentationId=presentation_id).execute()
    print("Slides in deck:")
    for i, slide in enumerate(presentation["slides"]):
        snippet = slide_text(slide).replace("\n", " ")[:60]
        print(f"  [{i}] {slide['objectId']}  -> {snippet!r}")

    slide_id = input("Slide ID to destroy (id shown above, or an index like 3): ").strip()
    if slide_id.isdigit():
        slide_id = presentation["slides"][int(slide_id)]["objectId"]
    slide_id = slide_id.strip()

    slide = confirm_target(presentation_id, slide_id)

    print("\nDESTROY SEQUENCE STARTED on", slide["objectId"])
    time.sleep(2)

    phase_spam(service, presentation_id, slide_id)
    pause()

    phase_crumble(service, presentation_id, slide_id, background_too=True)
    pause()

    phase_crumble(service, presentation_id, slide_id, background_too=True)
    pause()

    phase_scribble(service, presentation_id, slide_id)
    pause()

    phase_meltdown(service, presentation_id, slide_id)
    pause()

    delete_slide(service, presentation_id, slide_id)


if __name__ == "__main__":
    main()