import json
import os
import re

GRAPH_PATH = "data/ccpa_graph.json"

# Types that should never be cited as violations
BLOCKED_TYPES = {"Exemption", "Exemption_Expired", "Administrative", "Administrative_Procedure",
                 "Administrative/Investigatory", "Administrative_Authority", "Jurisdiction",
                 "Jurisdiction_Timeline", "Conflict_Resolution"}

class LegalVerifier:
    def __init__(self):
        self.graph = {}
        self.valid_sections = set()
        self.load_valid_sections()

    def load_valid_sections(self):
        if os.path.exists(GRAPH_PATH):
            with open(GRAPH_PATH, 'r', encoding='utf-8') as f:
                self.graph = json.load(f)
                self.valid_sections = set(self.graph.keys())

    def _is_citable(self, section_id: str) -> bool:
        """Returns True if this section is a citable violation (Right, Duty, Procedure, etc.)."""
        node_type = self.graph.get(section_id, {}).get("type", "")
        return node_type not in BLOCKED_TYPES

    def verify(self, harmful: bool, articles: list) -> list:
        if not harmful:
            return []

        clean_articles = []
        for article in articles:
            clean_name = str(article).replace("Section ", "").strip()

            # Exact match
            if clean_name in self.valid_sections:
                if self._is_citable(clean_name):
                    clean_articles.append(f"Section {clean_name}")
                continue

            # Handle sub-section citations like "1798.106(a)" → try "1798.106"
            base_match = re.match(r"(1798\.\d+(?:\(\w+\))*(?:\(\d+\))?)", clean_name)
            if base_match:
                candidate = base_match.group(1)
                if candidate in self.valid_sections and self._is_citable(candidate):
                    clean_articles.append(f"Section {candidate}")
                    continue
                # Strip sub-section suffix and try base section number
                base_only = re.match(r"(1798\.\d+)", clean_name)
                if base_only:
                    base_section = base_only.group(1)
                    if base_section in self.valid_sections and self._is_citable(base_section):
                        clean_articles.append(f"Section {base_section}")

        # If every cited article was an exemption/admin section and got filtered out,
        # the LLM was citing the exemption as the reason it's safe — treat as compliant.
        # Return None to signal the caller to flip harmful=False.
        if not clean_articles:
            return None

        return list(set(clean_articles))


verifier = LegalVerifier()