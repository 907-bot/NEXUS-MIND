"""
TOON - Token Oriented Object Notation
A lightweight, human-readable serialization format for agent communication.

TOON Format Specification:
==========================

Basic Types:
- Strings:    "value" or 'value'
- Numbers:    42, 3.14, -5
- Booleans:   true, false
- Null:       null
- Arrays:     [item1, item2, ...]

Objects:      Use :name value pairs
Nested:       :child :object ... :end

Example TOON:
-------------
:message :object
  :type "event"
  :agent "Orchestrator"
  :data :object
    :session_id "abc123"
    :timestamp 1699999999.0
  :end
:end

Compact Inline:
---------------
{name: "test", age: 30}

Tokens (for parsing):
  :object ... :end    - Object structure
  :array ... :end     - Array structure (optional markers)
  :name              - Key definition
  [ ]                - Array delimiters
  { }                - Inline object delimiters
"""

import re
from typing import Any, Union


class ToonEncoder:
    """Encode Python objects to TOON string format."""
    
    @staticmethod
    def encode(obj: Any, indent: int = 0, inline: bool = False) -> str:
        """
        Encode a Python object to TOON format.
        
        Args:
            obj: Python object to encode
            indent: Current indentation level
            inline: If True, use compact inline format for small objects
        """
        if obj is None:
            return "null"
        elif isinstance(obj, bool):
            return "true" if obj else "false"
        elif isinstance(obj, (int, float)):
            # Handle special floats
            if isinstance(obj, float) and (obj != obj or obj == float('inf')):
                return f'"{obj}"'  # Quote NaN/inf
            return str(obj)
        elif isinstance(obj, str):
            return f'"{obj}"'
        elif isinstance(obj, dict):
            return ToonEncoder._encode_dict(obj, indent, inline)
        elif isinstance(obj, (list, tuple)):
            return ToonEncoder._encode_array(obj, indent)
        else:
            # Fallback for other types
            return f'"{str(obj)}"'
    
    @staticmethod
    def _encode_dict(obj: dict, indent: int, inline: bool) -> str:
        """Encode a dictionary to TOON format."""
        if not obj:
            return "{}"
        
        # Check if can use inline format (small, simple values)
        if inline and all(
            isinstance(v, (str, int, float, bool, type(None))) 
            for v in obj.values()
        ):
            pairs = [f'{ToonEncoder._format_key(k)}: {ToonEncoder.encode(v, 0, True)}' 
                     for k, v in obj.items()]
            return "{ " + ", ".join(pairs) + " }"
        
        # Full TOON format
        spaces = "  " * indent
        next_indent = indent + 1
        lines = []
        
        for key, value in obj.items():
            key_str = ToonEncoder._format_key(key)
            
            if isinstance(value, dict) and value:
                lines.append(f"{spaces}{key_str} :object")
                lines.append(ToonEncoder._encode_dict(value, next_indent, False))
                lines.append(f"{spaces}:end")
            elif isinstance(value, (list, tuple)) and value:
                lines.append(f"{spaces}{key_str} {ToonEncoder._encode_array(value, next_indent)}")
            else:
                lines.append(f"{spaces}{key_str} {ToonEncoder.encode(value, next_indent, True)}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _encode_array(arr: Union[list, tuple], indent: int) -> str:
        """Encode an array to TOON format."""
        if not arr:
            return "[]"
        
        # Check if simple array (primitives only)
        all_simple = all(
            isinstance(item, (str, int, float, bool, type(None))) 
            for item in arr
        )
        
        if all_simple:
            items = [ToonEncoder.encode(item, 0, True) for item in arr]
            return "[" + ", ".join(items) + "]"
        
        # Complex array with nested structures
        spaces = "  " * indent
        lines = ["["]
        for item in arr:
            if isinstance(item, dict):
                lines.append(f"{spaces}  " + ToonEncoder._encode_dict(item, indent + 1, False).replace("\n", "\n" + ("  " * (indent + 1))))
                lines.append(f"{spaces}  ,")
            else:
                lines.append(f"{spaces}  {ToonEncoder.encode(item, indent + 1, True)},")
        
        # Remove trailing comma
        if lines[-1].endswith(","):
            lines[-1] = lines[-1][:-1]
        lines.append(f"{spaces}]")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_key(key: str) -> str:
        """Format a dictionary key for TOON."""
        # If key contains special chars, quote it
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(key)):
            return f":{key}"
        else:
            return f':"{key}"'


class ToonDecoder:
    """Decode TOON string format to Python objects."""
    
    @staticmethod
    def decode(toon_str: str) -> Any:
        """
        Decode a TOON string to Python object.
        Supports both TOON format and JSON for compatibility.
        """
        if not toon_str or not toon_str.strip():
            return None
        
        toon_str = toon_str.strip()
        
        # Try JSON first for compatibility
        if (toon_str.startswith('{') and toon_str.endswith('}')) or \
           (toon_str.startswith('[') and toon_str.endswith(']')):
            try:
                import json
                return json.loads(toon_str)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Parse TOON format
        return ToonDecoder._parse_toon(toon_str)
    
    @staticmethod
    def _parse_toon(toon_str: str) -> Any:
        """Parse TOON format string to Python object."""
        toon_str = toon_str.strip()
        
        # Empty
        if not toon_str:
            return None
        
        # Null
        if toon_str == "null":
            return None
        
        # Boolean
        if toon_str == "true":
            return True
        if toon_str == "false":
            return False
        
        # Number
        try:
            if '.' in toon_str:
                return float(toon_str)
            return int(toon_str)
        except ValueError:
            pass
        
        # Quoted string
        if (toon_str.startswith('"') and toon_str.endswith('"')) or \
           (toon_str.startswith("'") and toon_str.endswith("'")):
            return toon_str[1:-1]
        
        # Array
        if toon_str.startswith('[') and toon_str.endswith(']'):
            return ToonDecoder._parse_array(toon_str[1:-1])
        
        # Object (inline)
        if toon_str.startswith('{') and toon_str.endswith('}'):
            return ToonDecoder._parse_inline_object(toon_str[1:-1])
        
        # Full TOON object
        if toon_str.startswith(':') and ':object' in toon_str:
            return ToonDecoder._parse_full_object(toon_str)
        
        return toon_str
    
    @staticmethod
    def _parse_array(content: str) -> list:
        """Parse TOON array content."""
        if not content.strip():
            return []
        
        result = []
        current = ""
        depth = 0
        in_string = False
        escape = False
        
        for char in content:
            if escape:
                current += char
                escape = False
                continue
            
            if char == '\\':
                escape = True
                current += char
                continue
            
            if char == '"' or char == "'":
                in_string = not in_string
                current += char
                continue
            
            if in_string:
                current += char
                continue
            
            if char == '[':
                depth += 1
                current += char
            elif char == ']':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                item = current.strip()
                if item:
                    result.append(ToonDecoder._parse_toon(item))
                current = ""
            else:
                current += char
        
        # Add last item
        item = current.strip()
        if item:
            result.append(ToonDecoder._parse_toon(item))
        
        return result
    
    @staticmethod
    def _parse_inline_object(content: str) -> dict:
        """Parse inline object {key: value, ...}."""
        if not content.strip():
            return {}
        
        result = {}
        current = ""
        in_string = False
        escape = False
        expect_key = True
        current_key = None
        
        for char in content:
            if escape:
                current += char
                escape = False
                continue
            
            if char == '\\':
                escape = True
                current += char
                continue
            
            if char == '"' or char == "'":
                in_string = not in_string
                current += char
                continue
            
            if in_string:
                current += char
                continue
            
            if expect_key:
                if char == ':':
                    key = current.strip()
                    # Remove leading colon if present
                    if key.startswith(':'):
                        key = key[1:]
                    # Remove quotes if present
                    if (key.startswith('"') and key.endswith('"')) or \
                       (key.startswith("'") and key.endswith("'")):
                        key = key[1:-1]
                    current_key = key
                    current = ""
                    expect_key = False
                elif char in ' \t':
                    current += char
                else:
                    current += char
            else:
                if char == ',':
                    value = current.strip()
                    if current_key and value:
                        result[current_key] = ToonDecoder._parse_toon(value)
                    current_key = None
                    current = ""
                    expect_key = True
                elif char == '}':
                    # End of object
                    value = current.strip()
                    if current_key and value:
                        result[current_key] = ToonDecoder._parse_toon(value)
                else:
                    current += char
        
        return result
    
    @staticmethod
    def _parse_full_object(toon_str: str) -> dict:
        """Parse full TOON object format."""
        result = {}
        lines = toon_str.split('\n')
        ToonDecoder._parse_lines(lines, result)
        return result
    
    @staticmethod
    def _parse_lines(lines: list, result: dict, parent_result=None):
        """Recursively parse TOON lines."""
        i = 0
        current_parent = parent_result or result
        
        while i < len(lines):
            line = lines[i].rstrip()
            
            if not line.strip() or line.strip().startswith('#'):
                i += 1
                continue
            
            # End marker
            if line.strip() == ':end':
                break
            
            # Parse key-value
            parts = line.split(None, 1)
            if len(parts) < 2:
                i += 1
                continue
            
            key_part = parts[0]
            rest = parts[1] if len(parts) > 1 else ""
            
            # Extract key name
            key_match = re.match(r':?"?([^":\s]+)"?', key_part)
            if not key_match:
                i += 1
                continue
            key = key_match.group(1)
            
            rest = rest.strip()
            
            # Check for nested object
            if rest == ':object':
                # Nested object
                nested = {}
                i += 1
                ToonDecoder._parse_lines(lines[i:], nested, current_parent)
                current_parent[key] = nested
            elif rest.startswith('['):
                # Array
                # Find matching ]
                depth = 0
                arr_content = ""
                for c in rest:
                    if c == '[':
                        depth += 1
                        if depth == 1:
                            continue
                    elif c == ']':
                        depth -= 1
                        if depth == 0:
                            break
                    if depth > 0 or c != '[':
                        arr_content += c
                current_parent[key] = ToonDecoder._parse_array(arr_content)
            elif rest.startswith('{'):
                # Inline object
                current_parent[key] = ToonDecoder._parse_inline_object(rest)
            elif rest:
                # Simple value
                current_parent[key] = ToonDecoder._parse_toon(rest)
            
            i += 1


def dumps(obj: Any, compact: bool = False) -> str:
    """Encode Python object to TOON string."""
    if compact:
        # Use compact inline format
        return ToonEncoder.encode(obj, inline=True)
    return ToonEncoder.encode(obj, inline=False)


def loads(toon_str: str) -> Any:
    """Decode TOON string to Python object."""
    return ToonDecoder.decode(toon_str)


def dump(obj: Any, fp, compact: bool = False):
    """Encode and write TOON to file-like object."""
    fp.write(dumps(obj, compact))


def load(fp) -> Any:
    """Read and decode TOON from file-like object."""
    return loads(fp.read())


# Compatibility aliases
encode = dumps
decode = loads
