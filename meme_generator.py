import textwrap

from PIL import Image, ImageDraw, ImageFont


class MemeGenerator:
    def create_fresco(self, message: str) -> Image.Image:
        img = Image.open("./assets/images/fresco.jpg")
        font = ImageFont.truetype("./assets/fonts/timesnewromanpsmt.ttf", 20)

        draw = ImageDraw.Draw(img)

        lines = textwrap.wrap(message, width=30)
        text = "\n".join(lines)

        x = 165
        bottom_y = 190

        bbox = draw.multiline_textbbox(
            (0, 0),
            text,
            font=font,
            spacing=4,
            align="center",
        )

        text_height = bbox[3] - bbox[1]

        draw.multiline_text(
            (x, bottom_y - text_height),
            text,
            fill="black",
            font=font,
            spacing=4,
            anchor="ms",
            align="center",
        )

        return img

    def create_demotivator(self, message: str, image_path: str) -> Image.Image:
        font = ImageFont.truetype("./assets/fonts/timesnewromanpsmt.ttf", 120)

        img = Image.open(image_path)
        img = img.resize((1576, 1479))

        template = Image.open("./assets/images/demotivator.jpg")
        template.paste(img, (134, 142))

        draw = ImageDraw.Draw(template)

        lines = textwrap.wrap(message, width=30)
        text = "\n".join(lines)

        draw.multiline_text(
            (925, 1800),
            text,
            fill="white",
            font=font,
            spacing=4,
            anchor="ms",
            align="center",
        )

        return template
