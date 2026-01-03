"""
Utility functions for LaTeX Resume Manager
Handles template rendering and PDF compilation
"""

import json
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


def escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters in text.
    Preserves intentional LaTeX commands like \textbf{}.
    """
    if not isinstance(text, str):
        return str(text)
    
    # Characters that need escaping in LaTeX (excluding backslash for commands)
    replacements = [
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    
    # First, protect common LaTeX commands
    protected_commands = [
        (r'\textbf{', '<<<TEXTBF>>>'),
        (r'\textit{', '<<<TEXTIT>>>'),
        (r'\emph{', '<<<EMPH>>>'),
        (r'\underline{', '<<<UNDERLINE>>>'),
        (r'\href{', '<<<HREF>>>'),
        (r'\\', '<<<NEWLINE>>>'),
        (r'\&', '<<<AMPERSAND>>>'),
        (r'\%', '<<<PERCENT>>>'),
        (r'\$', '<<<DOLLAR>>>'),
        (r'\_', '<<<UNDERSCORE>>>'),
    ]
    
    # Protect commands
    for cmd, placeholder in protected_commands:
        text = text.replace(cmd, placeholder)
    
    # Apply escapes
    for char, escaped in replacements:
        text = text.replace(char, escaped)
    
    # Restore protected commands
    for cmd, placeholder in protected_commands:
        text = text.replace(placeholder, cmd)
    
    return text


def load_resume_data(filepath: str = "resume_data.json") -> dict:
    """Load resume data from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_data()
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")


def save_resume_data(data: dict, filepath: str = "resume_data.json") -> None:
    """Save resume data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_default_data() -> dict:
    """Return default empty resume data structure."""
    return {
        "personal": {
            "name": "Your Name",
            "email": "email@example.com",
            "linkedin": "yourlinkedin",
            "portfolio": "https://yourportfolio.com"
        },
        "education": [],
        "blocks": [],
        "publications": [],
        "leadership": [],
        "skills": {
            "software": "",
            "tools": "",
            "fabrication": ""
        }
    }


def escape_data_recursive(obj, skip_keys=None):
    """Recursively escape all strings in a data structure for LaTeX.
    
    Args:
        obj: The object to escape
        skip_keys: Set of dictionary keys to skip escaping (e.g., URLs)
    """
    if skip_keys is None:
        skip_keys = {'portfolio', 'link', 'email', 'linkedin'}
    
    if isinstance(obj, str):
        return escape_latex(obj)
    elif isinstance(obj, dict):
        return {
            k: (v if k in skip_keys else escape_data_recursive(v, skip_keys))
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [escape_data_recursive(item, skip_keys) for item in obj]
    else:
        return obj


def render_latex(data: dict, template_path: str = "template.tex") -> str:
    """
    Render resume data into LaTeX using Jinja2 template.
    Uses custom delimiters to avoid conflicts with LaTeX syntax.
    """
    template_dir = os.path.dirname(os.path.abspath(template_path))
    template_name = os.path.basename(template_path)
    
    # Escape all strings in data for LaTeX
    escaped_data = escape_data_recursive(data)
    
    # Create Jinja2 environment with custom delimiters for LaTeX
    env = Environment(
        loader=FileSystemLoader(template_dir if template_dir else '.'),
        autoescape=False,
        block_start_string='((*',
        block_end_string='*))',
        variable_start_string='(((',
        variable_end_string=')))',
        comment_start_string='((#',
        comment_end_string='#))',
    )
    
    # Add custom filter for LaTeX escaping (in case needed in template)
    env.filters['escape_latex'] = escape_latex
    
    template = env.get_template(template_name)
    return template.render(**escaped_data)


def save_latex(content: str, output_path: str = "output.tex") -> None:
    """Save rendered LaTeX content to file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def compile_pdf(tex_path: str = "output.tex", output_dir: str = ".") -> tuple[bool, str]:
    """
    Compile LaTeX file to PDF using pdflatex.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    tex_path = Path(tex_path)
    output_dir = Path(output_dir)
    
    if not tex_path.exists():
        return False, f"TeX file not found: {tex_path}"
    
    # Check if pdflatex is available
    if not shutil.which('pdflatex'):
        return False, "pdflatex not found. Please install a LaTeX distribution (e.g., MacTeX, TeX Live)."
    
    try:
        # Run pdflatex twice for proper cross-references
        for i in range(2):
            result = subprocess.run(
                [
                    'pdflatex',
                    '-interaction=nonstopmode',
                    '-output-directory', str(output_dir),
                    str(tex_path)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
        
        pdf_path = output_dir / tex_path.with_suffix('.pdf').name
        
        if pdf_path.exists():
            return True, f"PDF generated successfully: {pdf_path}"
        else:
            # Extract error from log
            log_path = output_dir / tex_path.with_suffix('.log').name
            error_msg = "PDF generation failed."
            if log_path.exists():
                with open(log_path, 'r') as f:
                    log_content = f.read()
                    # Find error lines
                    error_lines = [l for l in log_content.split('\n') if l.startswith('!')]
                    if error_lines:
                        error_msg += f"\nErrors:\n" + '\n'.join(error_lines[:5])
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, "PDF compilation timed out (60 seconds)"
    except Exception as e:
        return False, f"Compilation error: {str(e)}"


def cleanup_aux_files(base_path: str = "output") -> None:
    """Remove auxiliary files generated by pdflatex."""
    extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk']
    base = Path(base_path)
    
    for ext in extensions:
        aux_file = base.with_suffix(ext)
        if aux_file.exists():
            try:
                aux_file.unlink()
            except Exception:
                pass


def save_version(data: dict, custom_name: str = None, versions_dir: str = "versions") -> str:
    """
    Save current resume data as a named version.
    
    Args:
        data: Resume data to save
        custom_name: Optional custom name for the version (e.g., "Google_Application")
        versions_dir: Directory to save versions
    
    Returns:
        str: Name of the saved version file
    """
    versions_path = Path(versions_dir)
    versions_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use custom name if provided, otherwise just timestamp
    if custom_name:
        # Sanitize the custom name (replace spaces, remove special chars)
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in custom_name)
        version_name = f"resume_{safe_name}_{timestamp}.json"
    else:
        version_name = f"resume_{timestamp}.json"
    
    version_path = versions_path / version_name
    
    with open(version_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return version_name


def list_versions(versions_dir: str = "versions") -> list[str]:
    """List all saved versions sorted by date (newest first)."""
    versions_path = Path(versions_dir)
    
    if not versions_path.exists():
        return []
    
    versions = [f.name for f in versions_path.glob("resume_*.json")]
    return sorted(versions, reverse=True)


def load_version(version_name: str, versions_dir: str = "versions") -> dict:
    """Load a specific version from the versions directory."""
    version_path = Path(versions_dir) / version_name
    
    if not version_path.exists():
        raise FileNotFoundError(f"Version not found: {version_name}")
    
    with open(version_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def delete_version(version_name: str, versions_dir: str = "versions") -> bool:
    """Delete a specific version."""
    version_path = Path(versions_dir) / version_name
    
    if version_path.exists():
        version_path.unlink()
        return True
    return False


def generate_block_id(block_type: str, existing_ids: list[str]) -> str:
    """Generate a unique ID for a new block."""
    prefix = "proj" if block_type == "project" else "exp"
    counter = 1
    
    while f"{prefix}-{counter}" in existing_ids:
        counter += 1
    
    return f"{prefix}-{counter}"


def move_block(blocks: list[dict], block_id: str, direction: str) -> list[dict]:
    """
    Move a block up or down in the list.
    
    Args:
        blocks: List of block dictionaries
        block_id: ID of the block to move
        direction: 'up' or 'down'
    
    Returns:
        Updated list with block moved
    """
    idx = next((i for i, b in enumerate(blocks) if b['id'] == block_id), None)
    
    if idx is None:
        return blocks
    
    if direction == 'up' and idx > 0:
        blocks[idx], blocks[idx - 1] = blocks[idx - 1], blocks[idx]
    elif direction == 'down' and idx < len(blocks) - 1:
        blocks[idx], blocks[idx + 1] = blocks[idx + 1], blocks[idx]
    
    return blocks

