#!/usr/bin/env python3
"""
Component Architecture Analysis Script
This script runs the Codebase KB tool with a focus on component architecture.
"""

import dotenv
import os
import argparse
from flow import create_tutorial_flow
from component_architecture_prompts import (
    IDENTIFY_COMPONENTS_PROMPT,
    ANALYZE_ARCHITECTURE_PROMPT,
    WRITE_ARCHITECTURE_CHAPTER_PROMPT
)

# Load environment variables
dotenv.load_dotenv()

# Default file patterns - focusing on code files, excluding tests and build artifacts
DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "Dockerfile",
    "Makefile", "*.yaml", "*.yml",
}

DEFAULT_EXCLUDE_PATTERNS = {
    "assets/*", "data/*", "examples/*", "images/*", "public/*", "static/*", "temp/*",
    "docs/*", 
    "venv/*", ".venv/*", "*test*", "tests/*", "docs/*", "examples/*", "v1/*",
    "dist/*", "build/*", "experimental/*", "deprecated/*", "misc/*", 
    "legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*", "obj/*", "bin/*", "node_modules/*", "*.log"
}

def patch_node_prompts():
    """
    Monkey patch the node classes to use our custom prompts.
    This is a temporary solution until we refactor the nodes to accept custom prompts.
    """
    from nodes import IdentifyAbstractions, AnalyzeRelationships, WriteChapters
    
    # Store original methods
    original_identify_exec = IdentifyAbstractions.exec
    original_analyze_exec = AnalyzeRelationships.exec
    original_write_exec = WriteChapters.exec
    
    # Create patched methods
    def patched_identify_exec(self, prep_res):
        """Patched version of IdentifyAbstractions.exec that uses our custom prompt"""
        (
            context,
            file_listing_for_prompt,
            file_count,
            project_name,
            language,
            use_cache,
            max_abstraction_num,
        ) = prep_res
        
        # Add language instruction and hints only if not English
        language_instruction = ""
        name_lang_hint = ""
        desc_lang_hint = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate the `name` and `description` for each abstraction in **{language.capitalize()}** language. Do NOT use English for these fields.\n\n"
            name_lang_hint = f" (value in {language.capitalize()})"
            desc_lang_hint = f" (value in {language.capitalize()})"
        
        # Use our custom prompt
        from utils.call_llm import call_llm
        import yaml
        
        print(f"Identifying architectural components using LLM...")
        
        prompt = IDENTIFY_COMPONENTS_PROMPT.format(
            project_name=project_name,
            context=context,
            language_instruction=language_instruction,
            name_lang_hint=name_lang_hint,
            desc_lang_hint=desc_lang_hint,
            file_listing_for_prompt=file_listing_for_prompt,
            max_abstraction_num=max_abstraction_num
        )
        
        response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))
        
        # The rest of the method is the same as the original
        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        abstractions = yaml.safe_load(yaml_str)

        if not isinstance(abstractions, list):
            raise ValueError("LLM Output is not a list")

        validated_abstractions = []
        for item in abstractions:
            if not isinstance(item, dict) or not all(
                k in item for k in ["name", "description", "file_indices"]
            ):
                raise ValueError(f"Missing keys in abstraction item: {item}")
            if not isinstance(item["name"], str):
                raise ValueError(f"Name is not a string in item: {item}")
            if not isinstance(item["description"], str):
                raise ValueError(f"Description is not a string in item: {item}")
            if not isinstance(item["file_indices"], list):
                raise ValueError(f"file_indices is not a list in item: {item}")

            # Validate indices
            validated_indices = []
            for idx_entry in item["file_indices"]:
                try:
                    if isinstance(idx_entry, int):
                        idx = idx_entry
                    elif isinstance(idx_entry, str) and "#" in idx_entry:
                        idx = int(idx_entry.split("#")[0].strip())
                    else:
                        idx = int(str(idx_entry).strip())

                    if not (0 <= idx < file_count):
                        raise ValueError(
                            f"Invalid file index {idx} found in item {item['name']}. Max index is {file_count - 1}."
                        )
                    validated_indices.append(idx)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Could not parse index from entry: {idx_entry} in item {item['name']}"
                    )

            item["files"] = sorted(list(set(validated_indices)))
            # Store only the required fields
            validated_abstractions.append(
                {
                    "name": item["name"],  # Potentially translated name
                    "description": item[
                        "description"
                    ],  # Potentially translated description
                    "files": item["files"],
                }
            )

        print(f"Identified {len(validated_abstractions)} architectural components.")
        return validated_abstractions
    
    def patched_analyze_exec(self, prep_res):
        """Patched version of AnalyzeRelationships.exec that uses our custom prompt"""
        (
            context,
            abstraction_listing,
            num_abstractions,
            project_name,
            language,
            use_cache,
        ) = prep_res
        
        print(f"Analyzing architectural relationships using LLM...")
        
        # Add language instruction and hints only if not English
        language_instruction = ""
        lang_hint = ""
        list_lang_note = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate the `summary` and relationship `label` fields in **{language.capitalize()}** language. Do NOT use English for these fields.\n\n"
            lang_hint = f" (in {language.capitalize()})"
            list_lang_note = f" (Names might be in {language.capitalize()})"
        
        # Use our custom prompt
        from utils.call_llm import call_llm
        import yaml
        
        prompt = ANALYZE_ARCHITECTURE_PROMPT.format(
            project_name=project_name,
            abstraction_listing=abstraction_listing,
            context=context,
            language_instruction=language_instruction,
            lang_hint=lang_hint,
            list_lang_note=list_lang_note
        )
        
        response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))
        
        # The rest of the method is the same as the original
        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        relationships_data = yaml.safe_load(yaml_str)

        if not isinstance(relationships_data, dict) or not all(
            k in relationships_data for k in ["summary", "relationships"]
        ):
            raise ValueError(
                "LLM output is not a dict or missing keys ('summary', 'relationships')"
            )
        if not isinstance(relationships_data["summary"], str):
            raise ValueError("summary is not a string")
        if not isinstance(relationships_data["relationships"], list):
            raise ValueError("relationships is not a list")

        # Validate relationships structure
        validated_relationships = []
        for rel in relationships_data["relationships"]:
            # Check for 'label' key
            if not isinstance(rel, dict) or not all(
                k in rel for k in ["from_abstraction", "to_abstraction", "label"]
            ):
                raise ValueError(
                    f"Missing keys (expected from_abstraction, to_abstraction, label) in relationship item: {rel}"
                )
            # Validate 'label' is a string
            if not isinstance(rel["label"], str):
                raise ValueError(f"Relationship label is not a string: {rel}")

            # Validate indices
            try:
                from_idx = int(str(rel["from_abstraction"]).split("#")[0].strip())
                to_idx = int(str(rel["to_abstraction"]).split("#")[0].strip())
                if not (
                    0 <= from_idx < num_abstractions and 0 <= to_idx < num_abstractions
                ):
                    raise ValueError(
                        f"Invalid index in relationship: from={from_idx}, to={to_idx}. Max index is {num_abstractions-1}."
                    )
                validated_relationships.append(
                    {
                        "from": from_idx,
                        "to": to_idx,
                        "label": rel["label"],  # Potentially translated label
                    }
                )
            except (ValueError, TypeError):
                raise ValueError(f"Could not parse indices from relationship: {rel}")

        print("Generated architectural summary and relationship details.")
        return {
            "summary": relationships_data["summary"],
            "details": validated_relationships,
        }
    
    def patched_write_exec(self, item):
        """Patched version of WriteChapters.exec that uses our custom prompt"""
        (
            abstraction_index,
            abstraction_name,
            abstraction_description,
            related_abstractions,
            context,
            chapter_num,
            project_name,
            language,
            use_cache,
        ) = item
        
        print(f"Writing chapter {chapter_num} for '{abstraction_name}'...")
        
        # Add language instruction only if not English
        language_instruction = ""
        chapter_content_note = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Write the entire chapter content in **{language.capitalize()}** language. Do NOT use English.\n\n"
            chapter_content_note = f"REMINDER: Write all content in {language.capitalize()}, not in English."
        
        # Use our custom prompt
        from utils.call_llm import call_llm
        
        prompt = WRITE_ARCHITECTURE_CHAPTER_PROMPT.format(
            project_name=project_name,
            abstraction_name=abstraction_name,
            abstraction_description=abstraction_description,
            related_abstractions=related_abstractions,
            context=context,
            chapter_num=chapter_num,
            language_instruction=language_instruction,
            chapter_content_note=chapter_content_note
        )
        
        chapter_content = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))
        
        # Simple validation - check if the content starts with expected header
        expected_header_prefix = f"# Chapter {chapter_num}:"
        if not chapter_content.strip().startswith(expected_header_prefix):
            print(f"Warning: Chapter content doesn't start with expected header '{expected_header_prefix}'")
            # Add the header if missing
            chapter_content = f"# Chapter {chapter_num}: {abstraction_name}\n\n{chapter_content}"
        
        return chapter_content
    
    # Apply the patches
    IdentifyAbstractions.exec = patched_identify_exec
    AnalyzeRelationships.exec = patched_analyze_exec
    WriteChapters.exec = patched_write_exec
    
    print("Node prompts patched to focus on component architecture.")

def main():
    parser = argparse.ArgumentParser(description="Generate component architecture documentation for a GitHub codebase or local directory.")

    # Create mutually exclusive group for source
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo", help="URL of the public GitHub repository.")
    source_group.add_argument("--dir", help="Path to local directory.")

    parser.add_argument("-n", "--name", help="Project name (optional, derived from repo/directory if omitted).")
    parser.add_argument("-t", "--token", help="GitHub personal access token (optional, reads from GITHUB_TOKEN env var if not provided).")
    parser.add_argument("-o", "--output", default="output/architecture", help="Base directory for output (default: ./output/architecture).")
    parser.add_argument("-i", "--include", nargs="+", help="Include file patterns (e.g. '*.py' '*.js'). Defaults to common code files if not specified.")
    parser.add_argument("-e", "--exclude", nargs="+", help="Exclude file patterns (e.g. 'tests/*' 'docs/*'). Defaults to test/build directories if not specified.")
    parser.add_argument("-s", "--max-size", type=int, default=100000, help="Maximum file size in bytes (default: 100000, about 100KB).")
    parser.add_argument("--language", default="english", help="Language for the generated documentation (default: english)")
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM response caching (default: caching enabled)")
    parser.add_argument("--max-abstractions", type=int, default=10, help="Maximum number of architectural components to identify (default: 10)")

    args = parser.parse_args()

    # Get GitHub token from argument or environment variable if using repo
    github_token = None
    if args.repo:
        github_token = args.token or os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("Warning: No GitHub token provided. You might hit rate limits for public repositories.")

    # Initialize the shared dictionary with inputs
    shared = {
        "repo_url": args.repo,
        "local_dir": args.dir,
        "project_name": args.name,  # Can be None, FetchRepo will derive it
        "github_token": github_token,
        "output_dir": args.output,  # Base directory for CombineTutorial output

        # Add include/exclude patterns and max file size
        "include_patterns": set(args.include) if args.include else DEFAULT_INCLUDE_PATTERNS,
        "exclude_patterns": set(args.exclude) if args.exclude else DEFAULT_EXCLUDE_PATTERNS,
        "max_file_size": args.max_size,

        # Add language for multi-language support
        "language": args.language,
        
        # Add use_cache flag (inverse of no-cache flag)
        "use_cache": not args.no_cache,
        
        # Add max_abstraction_num parameter
        "max_abstraction_num": args.max_abstractions,

        # Outputs will be populated by the nodes
        "files": [],
        "abstractions": [],
        "relationships": {},
        "chapter_order": [],
        "chapters": [],
        "final_output_dir": None
    }

    # Patch the node prompts to focus on component architecture
    patch_node_prompts()

    # Display starting message
    print(f"Starting component architecture analysis for: {args.repo or args.dir} in {args.language.capitalize()} language")
    print(f"LLM caching: {'Disabled' if args.no_cache else 'Enabled'}")

    # Create the flow instance
    tutorial_flow = create_tutorial_flow()

    # Run the flow
    tutorial_flow.run(shared)
    
    print(f"\nComponent architecture analysis complete! Files are in: {shared['final_output_dir']}")

if __name__ == "__main__":
    main()
