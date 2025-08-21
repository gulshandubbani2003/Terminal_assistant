import os
import re
from .model_manager import ModelManager


class CommandGenerator:
    def __init__(self):
        self.manager = ModelManager()
    
    def generate_commands(self, query, context=None):
        try:
            prompt = self._build_prompt(query, context)
            response = self.manager.generate(prompt)
            
            # Check if response contains thinking tokens
            has_thinking = '<think>' in response and '</think>' in response
            
            if has_thinking:
                thoughts = []
                remaining_response = response
                while '<think>' in remaining_response and '</think>' in remaining_response:
                    think_start = remaining_response.find('<think>') + len('<think>')
                    think_end = remaining_response.find('</think>')
                    if think_start > -1 and think_end > -1:
                        thought = remaining_response[think_start:think_end].strip()
                        thoughts.append(thought)
                        remaining_response = remaining_response[think_end + len('</think>'):]
                
                final_response = remaining_response.strip()
                results = self._format_thinking_response(thoughts, final_response)
                return self._apply_safety_filters(query, results, context)
            else:
                results = self._parse_response(response)
                return self._apply_safety_filters(query, results, context)
                
        except Exception as e:
            return [{
                'type': 'warning',
                'content': f"Error: {str(e)}"
            }, {
                'type': 'command',
                'content': None,
                'details': None
            }]

    def _build_prompt(self, query, context):
        # Determine the primary context based on the query and environment
        os_name = context.get('os', 'Linux')
        is_windows = 'Windows' in os_name or 'win' in os_name.lower()
        
        if is_windows:
            system_context = f"""SYSTEM: You are a Windows PowerShell/Command Prompt expert. Generate exactly ONE command or command sequence.
Primary focus is on Windows system operations (file operations, directory management, Windows-specific commands).
Only consider Git operations if the query explicitly mentions Git/repository operations.
    
USER QUERY: {query}
    
RESPONSE FORMAT:
🧠 Analysis: [1-line explanation]
🛠️ Command: ```[executable Windows command(s)]```
📝 Details: [technical specifics]
⚠️ Warning: [if dangerous]

CURRENT CONTEXT:
- OS: {context.get('os', 'Windows')}
- Directory: {context.get('cwd', 'Unknown')}
{f'- Git repo: Yes (only relevant for Git-specific queries)' if context.get('git') else ''}

PRIORITY ORDER:
1. Windows file system operations (dir, copy, move, del, etc.)
2. Windows system operations (systeminfo, tasklist, etc.)
3. Repository operations (only if explicitly requested)

EXAMPLES:
Query: "list all files in current directory"
🧠 Analysis: List all files and directories in the current directory using Windows command
🛠️ Command: ```dir```
📝 Details: Shows all files and directories with details like size, date, and attributes
⚠️ Warning: None

Query: "update git repo"
🧠 Analysis: Update local Git repository with remote changes
🛠️ Command: ```git pull origin main```
📝 Details: Fetches and merges changes from the remote repository
⚠️ Warning: Ensure working directory is clean before updating
"""
        else:
            system_context = f"""SYSTEM: You are a Linux terminal expert. Generate exactly ONE command or command sequence.
Primary focus is on system-level operations (package management, system updates, file operations).
Only consider Git operations if the query explicitly mentions Git/repository operations.
    
USER QUERY: {query}
    
RESPONSE FORMAT:
🧠 Analysis: [1-line explanation]
🛠️ Command: ```[executable command(s)]```
📝 Details: [technical specifics]
⚠️ Warning: [if dangerous]

CURRENT CONTEXT:
- OS: {context.get('os', 'Linux')}
- Directory: {context.get('cwd', 'Unknown')}
{f'- Git repo: Yes (only relevant for Git-specific queries)' if context.get('git') else ''}

PRIORITY ORDER:
1. System-level operations (apt, dnf, pacman, etc.)
2. File system operations
3. Repository operations (only if explicitly requested)

EXAMPLES:
Query: "update packages"
🧠 Analysis: Update system packages using the appropriate package manager
🛠️ Command: ```sudo apt update && sudo apt upgrade -y```
📝 Details: Updates package lists and upgrades all installed packages
⚠️ Warning: System may require restart after certain updates

Query: "update git repo"
🧠 Analysis: Update local Git repository with remote changes
🛠️ Command: ```git pull origin main```
📝 Details: Fetches and merges changes from the remote repository
⚠️ Warning: Ensure working directory is clean before updating
"""
        return system_context

    
    def _format_thinking_response(self, thoughts, final_response):
        results = []
        
        # Add thinking process to results
        for thought in thoughts:
            results.append({
                'type': 'thinking',
                'content': thought
            })
        
        # Parse the final response
        components = self._parse_response(final_response)
        
        # Clean up any duplicate sections caused by thinking process
        seen_types = set()
        cleaned_components = []
        
        for comp in components:
            if comp['type'] not in seen_types and comp['content']:
                seen_types.add(comp['type'])
                # Remove any duplicate content within the same component
                if isinstance(comp['content'], str):
                    comp['content'] = '\n'.join(dict.fromkeys(comp['content'].split('\n')))
                cleaned_components.append(comp)
        
        results.extend(cleaned_components)
        return results
    
    
    def _parse_response(self, response):
        # Clean up response by removing any remaining XML-like tags
        cleaned = re.sub(r'<[^>]+>', '', response)
        
        components = {
            'analysis': None,
            'command': None,
            'details': None,
            'warning': None
        }
        
        markers = {
            'analysis': ['🧠', 'Analysis:'],
            'command': ['🛠️', 'Command:'],
            'details': ['📝', 'Details:'],
            'warning': ['⚠️', 'Warning:']
        }
        
        lines = cleaned.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for section, section_markers in markers.items():
                if any(marker in line for marker in section_markers):
                    current_section = section
                    for marker in section_markers:
                        line = line.replace(marker, '').strip()
                    components[section] = line
                    break
            
            if current_section and not any(
                marker in line for markers_list in markers.values() 
                for marker in markers_list
            ):
                if components[current_section]:
                    components[current_section] += '\n' + line
                else:
                    components[current_section] = line
        
        return [{
            'type': key,
            'content': '\n'.join(dict.fromkeys(value.strip().split('\n'))) if value else None
        } for key, value in components.items()]

    # --- Safety guardrails -------------------------------------------------
    def _apply_safety_filters(self, query, results, context):
        """Post-process model output to prevent destructive commands for benign intents.

        - If the user intent is to list/show/display, force a safe list command
          and replace any destructive or unrelated suggestions.
        - Adds a warning when a destructive command is replaced.
        """
        if not results:
            return results

        # Locate command, analysis, details items
        command_item = next((r for r in results if r.get('type') == 'command'), None)
        analysis_item = next((r for r in results if r.get('type') == 'analysis'), None)
        details_item = next((r for r in results if r.get('type') == 'details'), None)
        warning_item = next((r for r in results if r.get('type') == 'warning'), None)

        query_l = (query or '').lower()
        os_name = (context or {}).get('os', 'Linux') if context else 'Linux'
        is_windows = 'windows' in os_name.lower() or 'win' in os_name.lower()

        list_intent_keywords = [
            'list', 'show', 'display', 'view', 'enumerate', 'see files', 'see all files', 'ls', 'dir'
        ]
        destructive_terms = [
            'del', 'erase', 'rd', 'rmdir', 'rm', 'mv', 'move', 'ren', 'rename', 'format', 'mkfs',
            'shred', 'sdelete', 'rm -rf', 'Remove-Item', 'New-Item -Force'
        ]
        destructive_intent_terms = [
            'delete', 'remove', 'clean', 'cleanup', 'erase', 'wipe', 'trash', 'empty', 'purge'
        ]

        list_intent = any(k in query_l for k in list_intent_keywords) and not any(
            k in query_l for k in destructive_intent_terms
        )

        if command_item and (list_intent or not command_item.get('content')):
            cmd = (command_item.get('content') or '').lower()
            looks_destructive = any(term.lower() in cmd for term in destructive_terms)

            # Allow-list of safe list commands
            allowed_list_cmds = ['dir', 'ls', 'ls -la', 'ls -l', 'get-childitem', 'powershell get-childitem']
            is_already_listing = any(x in cmd for x in allowed_list_cmds)

            if list_intent and (looks_destructive or not is_already_listing):
                safe_cmd = 'dir' if is_windows else 'ls -la'
                # Replace command
                command_item['content'] = safe_cmd

                # Update analysis/details
                if analysis_item:
                    analysis_item['content'] = 'List all files and directories in the current directory.'
                if details_item:
                    details_item['content'] = (
                        "The 'dir' command lists directory contents on Windows."
                        if is_windows else
                        "The 'ls -la' command lists all files (including hidden) with details on Linux."
                    )

                # Add/augment warning if we replaced a destructive suggestion
                if looks_destructive:
                    warn_text = (
                        'Original suggestion looked destructive for a list intent; replaced with a safe listing command.'
                    )
                    if warning_item and warning_item.get('content'):
                        warning_item['content'] = f"{warning_item['content']}\n{warn_text}"
                    else:
                        results.append({'type': 'warning', 'content': warn_text})

        return results