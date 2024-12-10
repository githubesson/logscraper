import os
import readline
from src.core.modes.base import BaseMode

class ManualMode(BaseMode):
    """Manual mode for processing individual files."""

    def _complete_path(self, text, state):
        """Provide path completion for readline."""
        if "~" in text:
            text = os.path.expanduser(text)

        if os.path.isdir(text):
            current_dir = text
            file_prefix = ""
        else:
            current_dir = os.path.dirname(text) or "."
            file_prefix = os.path.basename(text)

        try:
            files = os.listdir(current_dir)
            if file_prefix:
                files = [f for f in files if f.startswith(file_prefix)]

            files = [os.path.join(current_dir, f) for f in files]
            files = [f + "/" if os.path.isdir(f) else f for f in files]
            return files[state]
        except (OSError, IndexError):
            return None

    async def run(self):
        try:
            # Setup readline with path completion
            readline.set_completer_delims(' \t\n;')
            readline.parse_and_bind("tab: complete")
            readline.set_completer(self._complete_path)

            file_path = input("Enter the path to the text file containing combos: ")
            channel_type = input("Enter the data type (archive/combo): ")
            
            if not os.path.exists(file_path):
                self.logger.error("File not found")
                return
            
            if channel_type not in ['archive', 'combo']:
                self.logger.error("Invalid channel type. Must be 'archive' or 'combo'")
                return

            password = None
            if channel_type == 'archive':
                password = input("Enter the password for the archive (leave blank if none): ")
                if not password:
                    password = None

            self.logger.info(f"Manual ingestion started for file: {file_path}")
            
            channel_info = {'type': channel_type}
            await self.process_worker.add_to_queue(file_path, password, channel_info)
            await self.process_worker.queue.join()
            
            self.logger.info("Manual ingestion completed")
            
        except Exception as e:
            self.logger.error(f"Error in manual mode: {e}")
        finally:
            readline.set_completer(None)
            await self.cleanup()