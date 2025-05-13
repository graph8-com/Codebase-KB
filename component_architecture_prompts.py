"""
Custom prompts for component architecture analysis.
These will be used to override the default prompts in the nodes.py file.
"""

# Modified prompt for IdentifyAbstractions to focus on component architecture
IDENTIFY_COMPONENTS_PROMPT = """
For the project `{project_name}`:

Codebase Context:
{context}

{language_instruction}Analyze the codebase context.
Identify the top 5-{max_abstraction_num} core architectural components in this system.
Focus specifically on:
1. Major system components and their roles
2. Service boundaries and interfaces
3. Key architectural patterns (MVC, microservices, etc.)
4. Core infrastructure components

For each component, provide:
1. A concise `name`{name_lang_hint} that clearly identifies the architectural component.
2. A technical `description` explaining its role in the system architecture, its responsibilities, and how it interacts with other components{desc_lang_hint}.
3. A list of relevant `file_indices` (integers) using the format `idx # path/comment`.

List of file indices and paths present in the context:
{file_listing_for_prompt}

Format the output as a YAML list of dictionaries:

```yaml
- name: |
  AuthenticationService{name_lang_hint}
  description: |
  Core authentication component responsible for user identity verification and session management.
  Implements OAuth2 flow and JWT token generation.{desc_lang_hint}
  file_indices:
  - 0 # auth/service.py
  - 3 # auth/middleware.py
- name: |
  DataAccessLayer{name_lang_hint}
  description: |
  Abstraction layer that handles database operations and provides a clean API for the business logic layer.
  Implements repository pattern to isolate data storage concerns.{desc_lang_hint}
  file_indices:
  - 5 # data/repositories.py
# ... up to {max_abstraction_num} components
```
"""

# Modified prompt for AnalyzeRelationships to focus on architectural relationships
ANALYZE_ARCHITECTURE_PROMPT = """
Based on the following architectural components and relevant code snippets from the project `{project_name}`:

List of Component Indices and Names{list_lang_note}:
{abstraction_listing}

Context (Components, Descriptions, Code):
{context}

{language_instruction}Please provide:
1. A high-level `summary` of the system architecture in a few technically precise sentences{lang_hint}. Use markdown formatting with **bold** and *italic* text to highlight important architectural patterns and design decisions.
2. A list (`relationships`) describing the key architectural relationships between these components. For each relationship, specify:
- `from_abstraction`: Index of the source component (e.g., `0 # ComponentName1`)
- `to_abstraction`: Index of the target component (e.g., `1 # ComponentName2`)
- `label`: A precise architectural relationship{lang_hint} (e.g., "Depends on", "Invokes", "Implements", "Extends", "Uses for routing", "Manages lifecycle", "Accesses").

IMPORTANT: Focus on architectural relationships like:
- Dependencies and dependency direction
- Control flow and message passing
- Inheritance and implementation
- Service consumption
- Data flow

Format the output as YAML:

```yaml
summary: |
  A technical description of the system architecture{lang_hint}.
  Highlight key **architectural patterns** and *design principles*.
relationships:
  - from_abstraction: 0 # ComponentName1
    to_abstraction: 1 # ComponentName2
    label: "Depends on"{lang_hint}
  - from_abstraction: 2 # ComponentName3
    to_abstraction: 0 # ComponentName1
    label: "Implements interface of"{lang_hint}
  # ... other relationships
```

Now, provide the YAML output:
"""

# Modified prompt for WriteChapters to focus on architectural documentation
WRITE_ARCHITECTURE_CHAPTER_PROMPT = """
You are writing a technical chapter about a specific architectural component for a software system documentation.

Project: {project_name}
Component: {abstraction_name}

Component Description:
{abstraction_description}

Related Components:
{related_abstractions}

Context (Code and Files):
{context}

{language_instruction}Write a comprehensive technical chapter about this architectural component. Your chapter should:

1. Start with a clear title using the format "# Chapter {chapter_num}: {abstraction_name}"
2. Begin with a brief introduction that explains what this component is and its role in the overall architecture
3. Include a "## Key Concepts" section that explains the core architectural principles and patterns used
4. Include a "## Component Interface" section that details how other components interact with this one
5. Include a "## Implementation Details" section with relevant code examples
6. If applicable, include a "## Dependencies" section listing what this component relies on
7. Use technical diagrams where helpful (using mermaid syntax)
8. End with a brief conclusion that ties this component back to the overall architecture

Use markdown formatting throughout. Include code snippets where relevant, using the appropriate language syntax highlighting.
Keep the total length between 500-1000 words.

{chapter_content_note}
"""
