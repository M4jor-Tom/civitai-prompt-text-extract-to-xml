#!./python

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import xml.dom.minidom

def parse_prompt(text: str) -> dict[str, str]:
    """Parses a CivitAI text-like prompt into structured data."""
    sections = {}

    # Extract positive prompt
    pos_prompt, neg_prompt = text.split("Negative prompt:")
    sections["positive-prompt"] = pos_prompt.strip()

    # Extract negative prompt
    neg_prompt, params = neg_prompt.split("Steps:", 1)
    sections["negative-prompt"] = neg_prompt.strip()

    # Extract parameters
    params_dict = {}
    for param in re.findall(r"(\w+): ([^,\n]+)", params):
        params_dict[param[0].strip().lower()] = param[1].strip()

    sections["parameters"] = params_dict
    return sections

def build_xml(data: dict[str, str]) -> ET.Element:
    """Builds an XML tree from parsed data."""
    root = ET.Element("civitai-ai-prompt")
    root = ET.Element("civitai-ai-prompt", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "https://raw.githubusercontent.com/M4jor-Tom/civitai_prompt.xsd/refs/heads/main/civitai_prompt.xsd"
    })

    # Prompt details
    prompt_details = ET.SubElement(root, "prompt-details")
    ET.SubElement(prompt_details, "positive-prompt").text = data["positive-prompt"]
    ET.SubElement(prompt_details, "negative-prompt").text = data["negative-prompt"]

    # Image parameters
    img_params = ET.SubElement(root, "image-parameters")
    for key in ["width", "height", "steps", "sampler", "cfg scale", "seed", "clip skip"]:
        if key in data["parameters"]:
            ET.SubElement(img_params, key.replace(" ", "-")).text = data["parameters"][key]
    
    # Resources
    resources = ET.SubElement(root, "resources")
    base_model = ET.SubElement(resources, "base-model")
    ET.SubElement(base_model, "id").text = data["parameters"].get("basemodel", "Unknown")

    return root

def save_xml(root: ET.Element, filename: str):
    """Saves XML tree to a file with proper formatting and indentation."""
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed_xml = xml.dom.minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")

    with open(filename, "w", encoding="utf-8") as file:
        file.write(pretty_xml)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The civitai text prompt file to transform to xml")
    parser.add_argument("text_prompt_path", type=str, help="The path to the file extracted from civitai when copying an image's prompt")
    parser.add_argument("xml_prompt_path", type=str, help="The path to the file created for civitai")
    args = parser.parse_args()
    with open(args.text_prompt_path, "r", encoding="utf-8") as text_prompt_file:
        text_prompt = text_prompt_file.read()
        parsed_data = parse_prompt(text_prompt)
        xml_root = build_xml(parsed_data)
        save_xml(xml_root, args.xml_prompt_path)
