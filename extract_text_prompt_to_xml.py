#!./python

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import xml.dom.minidom

def parse_prompt(text: str) -> dict[str, str]:
    """Parses a CivitAI text-like prompt into structured data."""

    known_keys = {
        "steps", "basemodel", "quantity", "width", "height", "seed", 
        "draft", "nsfw", "workflow", "clip skip", "cfg scale", "sampler", "fluxmode"
    }

    sections = {}

    # Extract positive and negative prompts
    if "Steps:" not in text:
        raise ValueError("Steps missing in text prompt")

    pos_prompt = ""
    neg_prompt = ""
    param_section = ""
    if "Negative prompt:" in text:
        pos_prompt, rest = text.split("Negative prompt:", 1)
        sections["positive-prompt"] = pos_prompt.strip()
        neg_prompt, param_section = rest.split("Steps:", 1)
        sections["negative-prompt"] = neg_prompt.strip()
    else:
        pos_prompt, param_section = text.split("Steps:", 1)
        sections["positive-prompt"] = pos_prompt.strip()

    # Ensure "Steps" is captured first
    param_section = param_section.strip()
    if param_section.startswith(" "):  # Sometimes there's a space before the number
        param_section = param_section.lstrip()
    
    first_comma = param_section.find(",")
    
    if first_comma != -1:
        steps_value = param_section[:first_comma].strip()
        remaining_params = param_section[first_comma+1:].strip()
    else:
        steps_value = param_section.strip()
        remaining_params = ""

    params_dict = {"steps": steps_value}

    # Process remaining parameters
    param_lines = remaining_params.split(", ") if remaining_params else []

    for param in param_lines:
        if ":" in param:
            key, value = param.split(":", 1)
            key = key.strip().lower()
            if key in known_keys:
                params_dict[key] = value.strip()

    sections["parameters"] = params_dict
    return sections

def build_xml(data: dict[str, str]) -> ET.Element:
    """Builds an XML tree from parsed data."""
    root = ET.Element("civitai-ai-prompt", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "https://raw.githubusercontent.com/M4jor-Tom/civitai_prompt.xsd/refs/heads/main/civitai_prompt.xsd"
    })

    # Prompt details
    prompt_details = ET.SubElement(root, "prompt-details")
    ET.SubElement(prompt_details, "positive-prompt").text = data["positive-prompt"]
    if "negative-prompt" in data:
        ET.SubElement(prompt_details, "negative-prompt").text = data["negative-prompt"]

    # Image parameters
    img_params = ET.SubElement(root, "image-parameters")
    for key in ["width", "height", "steps", "sampler", "cfg scale", "seed", "clip skip"]:
        if key in data["parameters"]:
            ET.SubElement(img_params, key.replace(" ", "-")).text = data["parameters"][key]
    
    return root

def save_xml(root: ET.Element, filename: str):
    """Saves XML tree to a file with proper formatting and indentation."""
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed_xml = xml.dom.minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")

    with open(filename, "w", encoding="utf-8") as file:
        file.write(pretty_xml)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The CivitAI text prompt file to transform to XML")
    parser.add_argument("text_prompt_path", type=str, help="The path to the file extracted from CivitAI when copying an image's prompt")
    parser.add_argument("xml_prompt_path", type=str, help="The path to the file created for CivitAI")
    args = parser.parse_args()

    with open(args.text_prompt_path, "r", encoding="utf-8") as text_prompt_file:
        print("Converting " + args.text_prompt_path + " to " + args.xml_prompt_path)
        text_prompt = text_prompt_file.read()
        parsed_data = parse_prompt(text_prompt)
        xml_root = build_xml(parsed_data)
        save_xml(xml_root, args.xml_prompt_path)
