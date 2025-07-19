"""
Omni - AI-powered code generation and project-aware editing CLI tool

Integrates modular UI, memory, personality, and AST-based code editing.
"""
import os
import subprocess
import requests
import json
import sys
import re
import argparse
import ast
from datetime import datetime
import threading
import queue as Queue
import time
from typing import List, Dict, Optional
from rich import print
from rich.panel import Panel
from rich.console import Console
from rich.tree import Tree
from ui_manager import UIManager
from personality_manager import PersonalityManager
from memory_manager import MemoryManager
from code_editor import CodeEditor
DEFAULT_BACKEND = 'openrouter'
OLLAMA_MODEL = 'phi4-reasoning'
OPENROUTER_MODEL = 'tngtech/deepseek-r1t2-chimera:free'
DEFAULT_SAVE_DIR = os.path.expanduser('/mnt/ProjectData/omni/omni_saves/')
CONFIG_FILE = 'config.json'
MEMORY_FILE = 'memory.json'
OLLAMA_API_URL = 'http://localhost:11434/api/generate'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
OPENROUTER_MODELS_API_URL = 'https://openrouter.ai/api/v1/models'
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
current_backend = DEFAULT_BACKEND
current_model = (OLLAMA_MODEL if DEFAULT_BACKEND == 'ollama' else
    OPENROUTER_MODEL)
OLLAMA_MODELS = {'deepseek': 'deepseek-coder:6.7b', 'codellama':
    'codellama:13b', 'mistral': 'mistral:latest', 'llama2': 'llama2:latest',
    'phind': 'phind-codellama:34b'}
os.makedirs(DEFAULT_SAVE_DIR, exist_ok=True)
TEMPLATES = {'flask':
    """from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Hello, Flask!</h1>'

if __name__ == '__main__':
    app.run(debug=True)"""
    , 'html5':
    """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Page</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>"""
    , 'scraper':
    """import requests
from bs4 import BeautifulSoup

def scrape(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        print(soup.title.text)
    except Exception as e:
        print(f"[bold red]Error scraping {url}:[/] {e}")

if __name__ == "__main__":
    scrape("https://example.com")"""
    }
console = Console()
personality_manager = PersonalityManager(CONFIG_FILE)
memory_manager = MemoryManager(MEMORY_FILE)
ui_manager = UIManager()
last_query: Optional[str] = None
last_response: Optional[str] = None
last_code: Optional[str] = None


def start_ollama_server() ->None:
    if current_backend != 'ollama':
        return
    try:
        requests.get('http://localhost:11434', timeout=1)
    except requests.exceptions.ConnectionError:
        print('[cyan]Starting Ollama server...[/]')
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)


def query_llm(prompt: str) ->str:
    personality = personality_manager.get_current_personality()
    system_prompt = personality.get('system_prompt', '') if personality else ''
    memory_context = memory_manager.get_memory_context()
    full_prompt = f'{system_prompt}\n\n{memory_context}\n\nUser: {prompt}'
    with ui_manager.show_spinner('AI is listening and thinking...'):
        if current_backend == 'ollama':
            response = query_ollama(full_prompt)
        elif current_backend == 'openrouter':
            response = query_openrouter(full_prompt)
        else:
            response = '[bold red]Error:[/] Unknown backend'
    return response


def query_openrouter(prompt: str) ->str:
    if not OPENROUTER_API_KEY:
        return '[bold red]Error:[/] OPENROUTER_API_KEY not set.'
    headers = {'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json'}
    payload = {'model': current_model, 'messages': [{'role': 'user',
        'content': prompt}]}
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=
            payload, timeout=90)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        error_details = ''
        try:
            error_details = response.json()
        except:
            error_details = response.text if hasattr(response, 'text'
                ) else str(e)
        return (
            f'[bold red]OpenRouter Error:[/] {e}\n[dim]Details: {error_details}[/dim]'
            )


def query_ollama(prompt: str) ->str:
    payload = {'model': current_model, 'prompt': prompt, 'stream': False}
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=90)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f'[bold red]Ollama Error:[/] {e}'


def extract_code(text: str) ->List[tuple[str, str]]:
    matches = re.findall('```(\\w*)\\n([\\s\\S]*?)```', text)
    return [(lang or 'text', code.strip()) for lang, code in matches
        ] if matches else []


def list_models(args: list=None) ->None:
    if current_backend == 'ollama':
        print('[bold cyan]Popular Ollama Models:[/]')
        for name, model_id in OLLAMA_MODELS.items():
            print(
                f"{'⭐' if model_id == current_model else '  '} [yellow]{name:12}[/] → {model_id}"
                )
    elif current_backend == 'openrouter':
        list_openrouter_models(args or [])


def list_openrouter_models(args: list):
    try:
        from simple_term_menu import TerminalMenu
    except ImportError:
        ui_manager.show_error(
            "'simple-term-menu' is required. `pip install simple-term-menu`")
        return
    try:
        with ui_manager.show_spinner('Fetching models...'):
            response = requests.get(OPENROUTER_MODELS_API_URL)
            response.raise_for_status()
        api_models_data = response.json().get('data', [])
    except requests.RequestException as e:
        ui_manager.show_error(f'Error fetching models: {e}')
        return
    all_models, sources = [], set()
    for model_data in api_models_data:
        if (model_id := model_data.get('id')):
            sources.add(model_id.split('/')[0])
            pricing = model_data.get('pricing', {})
            is_free = pricing.get('prompt') == '0' and pricing.get('completion'
                ) == '0'
            all_models.append({'id': model_id, 'name': model_data.get(
                'name'), 'source': model_id.split('/')[0], 'is_free': is_free})
    all_models.sort(key=lambda x: (x['source'], x['name']))
    if args and args[0].lower() == 'sources':
        print('[bold cyan]Available Model Sources:[/]')
        [print(f'  [yellow]{s}[/]') for s in sorted(list(sources))]
        return
    models_to_display, title = all_models, 'Select an OpenRouter Model'
    if args:
        filter_keyword = args[0].lower()
        title = f"Select a Model from '{filter_keyword}'"
        models_to_display = [m for m in all_models if filter_keyword in m[
            'source'].lower()]
        if not models_to_display:
            ui_manager.show_error(f"No models for source: '{filter_keyword}'")
            return
    menu_entries = [
        f"{'⭐' if m['id'] == current_model else '  '} {m['name']} [dim]({m['id']}){' [green](FREE)[/]' if m['is_free'] else ''}[/dim]"
         for m in models_to_display]
    try:
        cursor_idx = next((i for i, m in enumerate(models_to_display) if m[
            'id'] == current_model), 0)
        chosen_index = TerminalMenu(menu_entries, title=f'{title}',
            cursor_index=cursor_idx, cycle_cursor=True, clear_screen=True
            ).show()
        if chosen_index is not None:
            set_model(models_to_display[chosen_index]['id'])
        else:
            print('Model selection cancelled.')
    except Exception as e:
        ui_manager.show_error(f'Menu display error: {e}')


def set_model(model_id: str) ->None:
    global current_model
    current_model = model_id
    ui_manager.show_success(f'Model set to: {current_model}')


def switch_backend(backend_name: str) ->None:
    global current_backend, current_model
    backend_name = backend_name.lower()
    if backend_name not in ['ollama', 'openrouter']:
        ui_manager.show_error(f'Unknown backend: {backend_name}')
        return
    current_backend = backend_name
    current_model = (OLLAMA_MODEL if backend_name == 'ollama' else
        OPENROUTER_MODEL)
    ui_manager.show_success(
        f'Switched to {backend_name} backend with model: {current_model}')
    if backend_name == 'ollama':
        start_ollama_server()


def generate_project_manifest(path: str) ->str:
    manifest = ''
    tree = Tree(f'[bold cyan]Project: {os.path.basename(path)}[/]')
    exclude_dirs = {'__pycache__', '.git', 'venv', 'node_modules', '.idea'}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.
            startswith('.')]
        relative_path = os.path.relpath(root, path)
        branch = tree
        if relative_path != '.':
            parts = relative_path.split(os.sep)
            for part in parts:
                child = next((c for c in branch.children if c.label ==
                    f'[magenta]{part}[/]'), None)
                if not child:
                    child = branch.add(f'[magenta]{part}[/]')
                branch = child
        for fname in sorted(files):
            ext = os.path.splitext(fname)[1]
            if ext not in ('.py', '.js', '.html', '.css', '.md', '.txt'):
                continue
            rel_path = os.path.join(relative_path, fname
                ) if relative_path != '.' else fname
            branch.add(f'[green]{fname}[/]' if ext == '.py' else
                f'[dim]{fname}[/]')
            manifest += f'File: {rel_path}\n\n'
    console.print(tree)
    return manifest.strip()


def look_command(path: str) ->None:
    if not os.path.exists(path):
        ui_manager.show_error(f'❌ Path not found: {path}')
        return
    if os.path.isdir(path):
        with ui_manager.show_spinner('Generating project manifest...'):
            manifest = generate_project_manifest(path)
        memory_manager.add_look_data(path, manifest)
        ui_manager.show_success('✅ Project manifest added to memory.')
    else:
        try:
            with ui_manager.show_spinner('Loading file...'):
                with open(path, 'r') as f:
                    content = f.read().strip()
            memory_manager.add_look_data(path, content)
            ui_manager.show_success('✅ File content added to memory.')
        except Exception as e:
            ui_manager.show_error(f'❌ Error reading file: {e}')

def get_project_root(self) -> Optional[str]:
    """Find the first directory path in the 'look' memory."""
    for item in self.memory.get('look', []):
        path = item['file']
        if os.path.isdir(path):
            return path
    return None

def resolve_file_path(path: str) -> Optional[str]:
    """Resolves a file path, checking CWD first, then against project root in memory."""
    # Check if the path as-is is valid (absolute or relative to CWD)
    if os.path.exists(path):
        return os.path.abspath(path)
    
    # If not found, check relative to the project root in memory
    project_root = memory_manager.get_project_root()
    if project_root:
        full_path = os.path.join(project_root, path)
        if os.path.exists(full_path):
            return full_path
    
    return None

def resolve_file_path(path: str) -> Optional[str]:
    """Resolves a file path, checking CWD first, then against project root in memory."""
    if os.path.exists(path):
        return os.path.abspath(path)
    
    project_root = memory_manager.get_project_root() # Uses the memory manager
    if project_root:
        full_path = os.path.join(project_root, path)
        if os.path.exists(full_path):
            return full_path
    
    return None
    
def handle_file_edit_command(file_path: str, instruction: str):
    global last_code
    
    resolved_path = resolve_file_path(file_path) # Uses the new helper
    if not resolved_path:
        ui_manager.show_error(f"File not found: {file_path}")
        return
    
    if resolved_path != os.path.abspath(file_path):
        ui_manager.show_success(f"Found '{file_path}' in project. Using: {resolved_path}")

    try:
        editor = CodeEditor(resolved_path)
    except (ValueError, FileNotFoundError) as e:
        ui_manager.show_error(str(e))
        return

    # Step 2: Have the AI identify which part of the file to edit
    elements = editor.list_elements()
    prompt1 = (f"User wants to edit '{os.path.basename(resolved_path)}' with instruction: '{instruction}'.\n"
               f"Available elements: {', '.join(elements) if elements else 'None'}.\n"
               "Which element should be edited? If a simple change is needed that doesn't fit one element, respond with 'FILE'. Respond with only the name.")
    with ui_manager.show_spinner("AI is analyzing file..."):
        element_to_edit = query_llm(prompt1).strip().splitlines()[0]
    
    if element_to_edit not in elements and element_to_edit.upper() != 'FILE':
        ui_manager.show_error(f"AI identified '{element_to_edit}', which is not a valid element. Aborting.")
        return

    # Step 3: Have the AI generate the new code for the identified part
    if element_to_edit.upper() == 'FILE':
        ui_manager.show_success("AI has chosen to edit the entire file.")
        original_snippet = editor.source_code
        prompt2 = (f"Rewrite the entire file `{os.path.basename(resolved_path)}` to perform this task: '{instruction}'.\n\n"
                   f"Original Code:\n```python\n{original_snippet}```\n\nProvide only the complete, updated code block for the entire file.")
    else:
        ui_manager.show_success(f"AI selected '{element_to_edit}' for editing.")
        original_snippet = editor.get_source_of(element_to_edit)
        prompt2 = (f"Rewrite the element `{element_to_edit}` from `{os.path.basename(resolved_path)}` for this task: '{instruction}'.\n\n"
                   f"Original Code:\n```python\n{original_snippet}```\n\n"
                   "Provide only the complete, updated code block. You may include necessary import statements at the top of the code block.")

    with ui_manager.show_spinner(f"AI is editing '{element_to_edit}'..."):
        response = query_llm(prompt2)
    
    code_blocks = extract_code(response)
    if not code_blocks:
        ui_manager.show_error("AI did not return a valid code block.")
        print(Panel(response, title="[yellow]AI's Raw Response[/]"))
        return
    
    new_code = code_blocks[0][1]
    
    # Step 4: Validate and apply the changes to the CodeEditor instance
    if element_to_edit.upper() == 'FILE':
        try:
            # For whole-file edits, we just replace the whole AST
            editor.tree = ast.parse(new_code)
        except SyntaxError as e:
            ui_manager.show_error(f"AI returned invalid Python syntax: {e}")
            print(Panel(response, title="[yellow]AI's Raw Response[/]"))
            return
    elif not editor.replace_element(element_to_edit, new_code):
        ui_manager.show_error("AI returned invalid code; could not be parsed or applied.")
        print(Panel(response, title="[yellow]AI's Raw Response[/]"))
        return

    # Step 5: Show the diff and ask for user confirmation
    if not (diff := editor.get_diff()):
        ui_manager.show_success("AI made no changes.")
        return
        
    print(Panel(diff, title=f"[bold yellow]Proposed Changes for {resolved_path}[/]"))
    if ui_manager.get_user_input("Apply changes? (y/n): ").lower() in ['yes', 'y']:
        editor.save_changes()
        last_code = editor.get_modified_source()  # Update in-memory code for 'run' command
        ui_manager.show_success(f"Changes saved to {resolved_path}.")
    else:
        ui_manager.show_error("Changes discarded.")

def handle_project_refactor_command(instruction: str):
    if not any(os.path.isdir(item['file']) for item in memory_manager.
        memory.get('look', [])):
        ui_manager.show_error(
            "No project context. Use 'look <directory>' first.")
        return
    plan_prompt = f"""You are a project manager AI. Based on the project context and user request, create a JSON plan of actions. The structure must be `{{"actions": [...]}}`. Actions can be 'MODIFY' or 'CREATE'.

### Project Context ###
{memory_manager.get_memory_context()}

### User Request ###
'{instruction}'

Respond with ONLY the JSON plan."""
    with ui_manager.show_spinner('AI is creating an execution plan...'):
        plan_str = query_llm(plan_prompt)
    try:
        plan = json.loads(re.search('\\{.*\\}', plan_str, re.DOTALL).group(0))
        actions = plan.get('actions', [])
        if not actions:
            raise ValueError("No 'actions' key found in plan.")
    except Exception as e:
        ui_manager.show_error(f'AI failed to generate a valid plan: {e}')
        print(Panel(plan_str, title="[yellow]AI's Invalid Plan[/]"))
        return
    ui_manager.show_success('AI has created a plan:')
    for i, action in enumerate(actions):
        print(
            f"  [cyan]{i + 1}. {action.get('type', 'N/A')}:[/] {action.get('file', '')}/{action.get('element', action.get('element_name', 'N/A'))} - {action.get('reason', action.get('description', ''))}"
            )
    if ui_manager.get_user_input('\nProceed? (y/n): ').lower() not in ['yes',
        'y']:
        ui_manager.show_error('Aborted.')
        return
    editors: Dict[str, CodeEditor] = {}
    project_base_path = next((l['file'] for l in memory_manager.memory[
        'look'] if os.path.isdir(l['file'])), '.')
    for action in actions:
        pass
    full_diff = '\n'.join(editor.get_diff() for editor in editors.values() if
        editor.get_diff())
    if not full_diff:
        ui_manager.show_success('AI made no changes.')
        return
    print(Panel(full_diff, title=
        '[bold yellow]Proposed Project-Wide Changes[/]'))
    if ui_manager.get_user_input('Apply all changes? (y/n): ').lower() in [
        'yes', 'y']:
        for editor in editors.values():
            editor.save_changes()
        ui_manager.show_success('✅ Project changes applied.')
    else:
        ui_manager.show_error('Changes discarded.')


def interactive_mode() ->None:
    global last_query, last_response, last_code
    print(Panel(
        """[bold cyan]Omni Interactive Mode[/]
[dim]Type 'help' for commands, 'exit' to quit.[/dim]"""
        , border_style='cyan'))
    personality_name = personality_manager.get_current_personality().get('name'
        , 'Default')
    refresh_status_panel(personality_name)
    while True:
        try:
            user_input = ui_manager.get_user_input('\n> ')
            if not user_input:
                continue
            command, *args = user_input.split(maxsplit=1)
            arg_str = args[0] if args else ''
            if command == 'exit':
                memory_manager.save_memory()
                print('[bold cyan]Goodbye![/]')
                break
            elif command == 'help':
                print(
                    """[bold]Commands:[/]

  [bold cyan]Core & Project Commands[/]
  [yellow]send <prompt>[/]        - Ask the LLM a question.
  [yellow]look <path>[/]          - Read file or scan directory into memory.
  [yellow]edit <file> "instr"[/] - Edit a specific file using AI.
  [yellow]refactor "instr"[/]    - Refactor project in memory based on instruction.

  [bold cyan]File & Code Management[/]
  [yellow]save <filename>[/]     - Save last AI response to a file.
  [yellow]list[/]               - List saved files.
  [yellow]run[/]                 - Run the last generated Python code.

  [bold cyan]Session & Config[/]
  [yellow]history[/]             - Show the full chat history.
  [yellow]memory clear[/]        - Clear the chat and file memory.
  [yellow]backend <name>[/]      - Switch AI backend (e.g., openrouter, ollama).
  [yellow]models [src][/]        - Interactively list and select models.
  [yellow]set model <id>[/]      - Set the model directly by its ID.
  [yellow]personality <cmd>[/]   - Manage AI personalities ('list', 'set', 'add').
"""
                    )
            elif command == 'send':
                last_query = arg_str
                response = query_llm(arg_str)
                last_response = response
                print(Panel(response, title='[cyan]Response[/]'))
                if (code_blocks := extract_code(response)):
                    last_code = code_blocks[0][1]
            elif command == 'look':
                look_command(arg_str)
            elif command == 'edit':
                try:
                    file_path, instruction = arg_str.split(' ', 1)
                    handle_file_edit_command(file_path.strip('"'),
                        instruction.strip('"'))
                except (ValueError, IndexError):
                    ui_manager.show_error(
                        'Usage: edit <file_path> "<instruction>"')
            elif command == 'refactor':
                if not arg_str:
                    ui_manager.show_error('Usage: refactor "<instruction>"')
                else:
                    handle_project_refactor_command(arg_str.strip('"'))
            elif command == 'models':
                list_models(arg_str.split())
            elif command == 'set' and arg_str.startswith('model '):
                set_model(arg_str[6:])
            elif command == 'backend':
                switch_backend(arg_str)
            elif command == 'history':
                ui_manager.display_history(memory_manager.get_memory_context())
            elif command == 'memory' and arg_str == 'clear':
                memory_manager.clear_memory()
                ui_manager.show_success('✅ Memory cleared')
            elif command == 'personality':
                p_args = arg_str.split(maxsplit=1)
                cmd = p_args[0] if p_args else ''
                p_arg_str = p_args[1] if len(p_args) > 1 else ''
                if cmd == 'list':
                    for p in personality_manager.list_personalities():
                        print(f"- {p['name']}: {p['description']}")
                elif cmd == 'set' and p_arg_str:
                    if personality_manager.set_current_personality(p_arg_str):
                        personality_name = p_arg_str
                        ui_manager.show_success(
                            f'Set personality to {personality_name}')
                    else:
                        ui_manager.show_error('Personality not found.')
                else:
                    ui_manager.show_error(
                        "Invalid personality command. Use 'list' or 'set <name>'."
                        )
            elif command == 'run':
                run_python_code()
            elif command == 'save':
                if last_response:
                    save_code(last_response, arg_str or
                        f"omni_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        )
                else:
                    ui_manager.show_error('No response to save.')
            elif command == 'list':
                files = sorted(os.listdir(DEFAULT_SAVE_DIR))
                print('\n'.join(f'  - {f}' for f in files) if files else
                    '[yellow]No saved files.[/]')
            else:
                ui_manager.show_error("Unknown command. Type 'help'.")
            refresh_status_panel(personality_name)
        except KeyboardInterrupt:
            memory_manager.save_memory()
            print('\n[bold cyan]Goodbye![/]')
            break
        except Exception as e:
            ui_manager.show_error(f'An unexpected error occurred: {e}')


def run_python_code() ->None:
    global last_code
    if not last_code:
        ui_manager.show_error('No Python code in memory to run.')
        return
    temp_file = os.path.join(DEFAULT_SAVE_DIR, 'temp_run.py')
    try:
        with open(temp_file, 'w') as f:
            f.write(last_code)
        print('[bold cyan]\n--- Running Code ---\n[/]')
        subprocess.run([sys.executable, temp_file], check=True)
        print('[bold cyan]\n--- Code Finished ---\n[/]')
    except Exception as e:
        ui_manager.show_error(f'Error running code: {e}')
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def save_code(content: str, filename: str) ->None:
    filepath = os.path.join(DEFAULT_SAVE_DIR, filename)
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        ui_manager.show_success(f'Saved to: {filepath}')
    except IOError as e:
        ui_manager.show_error(f'Error saving file: {e}')


def main() ->None:
    try:
        import astor
    except ImportError:
        print("[bold red]Error:[/] 'astor' is required. `pip install astor`")
        sys.exit(1)
    try:
        import simple_term_menu
    except ImportError:
        print(
            "[bold red]Error:[/] 'simple-term-menu' is required. `pip install simple-term-menu`"
            )
        sys.exit(1)
    parser = argparse.ArgumentParser(description=
        'Omni - AI-powered code tool', add_help=False)
    parser.add_argument('command', nargs='?', help='Main command.')
    parser.add_argument('args', nargs='*', help='Arguments for the command.')
    parser.add_argument('-h', '--help', action='store_true')
    args, _ = parser.parse_known_args()
    if args.help or not args.command:
        interactive_mode()
    elif args.command == 'look' and args.args:
        look_command(args.args[0])
    elif args.command == 'edit' and len(args.args) >= 2:
        handle_file_edit_command(args.args[0], ' '.join(args.args[1:]))
    elif args.command == 'models':
        list_models(args.args)
    else:
        interactive_mode()


def refresh_status_panel(personality_name: str) ->None:
    ui_manager.display_status_panel(personality_name, current_backend,
        current_model, len(memory_manager.memory.get('chat', [])), len(
        memory_manager.memory.get('look', [])))


if __name__ == '__main__':
    main()
