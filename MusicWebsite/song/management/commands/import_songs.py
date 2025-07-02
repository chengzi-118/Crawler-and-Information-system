import json
import os
import shutil
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from typing import Any, Dict, List, Optional
from argparse import ArgumentParser
from ...models import Song
from singer.models import Singer

class Command(BaseCommand):
    """
    Django management command to import scraped song data into the database.

    This command expects a root directory
    containing subfolders named by song ID,
    each holding a 'data.json' file with song metadata
    and an image file (e.g., 'pic.jpg').
    """
    # The 'help' attribute is the short description shown
    # when running 'python manage.py help import_data'
    help = (
        'Imports scraped song data from individual data.json files '
        'located in ID folders.'
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Adds command-line arguments for the import_data command.

        Args:
            parser (ArgumentParser): The parser to 
            which arguments will be added.
        """
        parser.add_argument(
            'song_data_root',
            type=str,
            help=(
                'The root directory containing song ID folders '
                '(e.g., D:\\code\\python\\BigHomework\\Song)'
            )
        )

        parser.add_argument(
            '--image_root',
            type=str,
            default='',
            help='Optional: Root directory for local image files.'
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        The main logic of the custom Django management command.

        This method:
        1. Validates the provided root directories.
        2. Discovers all 'data.json' files within the song data root.
        3. Imports or updates song data in a database transaction.
        4. Associates local image files with song records.
        5. Provides detailed progress and summary messages to the console.

        Args:
            *args (Any): Positional arguments passed to the command.
            **options (Any): Keyword arguments (from add_arguments)
            passed to the command.
        """
        song_data_root: str = options['song_data_root']
        image_root: str = options['image_root']

        # If --image_root is not provided,
        # assume it's the same as song_data_root
        if not image_root:
            image_root = song_data_root

        # --- Input Validation ---
        if not os.path.isdir(song_data_root):
            raise CommandError(
                self.style.ERROR(
                    f'Error: Song data root directory does not exist '
                    f'or is not a directory: {song_data_root}'
                )
            )

        # Display initial search message
        self.stdout.write(
            self.style.SUCCESS(
                f'Searching for data.json files in {song_data_root}...'
                )
        )

        json_files_to_process: List[str] = []

        # --- File Discovery ---
        # os.walk traverses the directory tree (root, subdirectories, files)
        for root, _, files in os.walk(song_data_root):
            # Check if 'data.json' exists in the current directory
            if 'data.json' in files:
                json_files_to_process.append(os.path.join(root, 'data.json'))

        if not json_files_to_process:
            raise CommandError(
                self.style.ERROR(
                    f'Error: No data.json files found in {song_data_root} '
                    f'or its subdirectories.'
                )
            )

        total_files: int = len(json_files_to_process)
        self.stdout.write(
            self.style.SUCCESS(
                f'Found {total_files} data.json files. Starting import...'
                )
        )

        # Initialize counters for import summary
        imported_songs_count: int = 0
        processed_images_count: int = 0
        missing_images_count: int = 0
        
        missing_lyric_list: list[int] = []

        # --- Data Import using Transaction ---
        # transaction.atomic() ensures that 
        # all database changes made within this block
        # are either fully committed or entirely rolled back
        # if any error occurs.
        # This prevents partial or inconsistent data in the database.
        with transaction.atomic():
            # Iterate through each discovered data.json file
            for i, json_file_path in enumerate(json_files_to_process):
                self.stdout.write(f'Processing file ('
                                  f'{i+1}/{total_files}): {json_file_path}')
                
                song_folder_path = os.path.dirname(json_file_path)
                try:
                    # Extract song ID from the folder name
                    song_id_from_path: str = os.path.basename(
                        os.path.dirname(json_file_path)
                    )
                    # Convert the string ID to an integer,
                    # as kuwo_id is an IntegerField
                    
                    song_kuwo_id: int = int(song_id_from_path)

                except ValueError:
                    # Log a warning and skip the file 
                    # if the folder name is not a valid ID
                    self.stdout.write(
                        self.style.WARNING(
                            'Skipping file with non-numeric'
                            ' parent folder name (expected ID): '
                            f'{json_file_path}.'
                        )
                    )
                    continue  # Move to the next file

                try:
                    # Open and load the JSON data for the current song
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        song_data: Dict[str, Any] = json.load(f)
                                                                               
                    # Validate if the ID in JSON matches the folder ID
                    if song_data.get('id') != song_kuwo_id:
                        self.stdout.write(
                            self.style.WARNING(
                                f' - ID mismatch for {json_file_path}'
                                f': Folder ID '
                                f'{song_kuwo_id} vs JSON ID '
                                f'{song_data.get("id")}. '
                                f'Using folder ID for consistency.'
                            )
                        )
                        # Correct the data to match the folder
                        # for consistency if needed
                        song_data['id'] = song_kuwo_id

                    original_pic_url: str = song_data.get('pic', '')
                    
                    # Find the song's singer based on 'artistid' from JSON
                    associated_singer = None
                    artist_id_from_json: int = song_data.get('artistid', -1)
                                                                                                                                                           
                    if artist_id_from_json != -1:
                        try:
                            # Attempt to get the singer by their kuwo_id
                            associated_singer = Singer.objects.get(
                                kuwo_id = artist_id_from_json
                            )
                        except Singer.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f' - Singer with kuwo_id {artist_id_from_json} '
                                f'for song "{song_data.get("name", "Unknown")}" '
                                f'not found in database.'
                                ' Song will be imported'
                                ' without a linked singer.'
                            ))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f' - Error finding singer for song "'
                                f'{song_data.get("name", "Unknown")}" '
                                f'(ID: {artist_id_from_json}): {e}'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f' - Song "{song_data.get("name", "Unknown")}"'
                            f' has invalid artist_id (-1). No singer linked.'
                        ))
                        
                    # Import comments
                    comments_raw = song_data.get('comments')
                    comments_list: List[Dict[str, Any]] = []
                    if comments_raw is not None:
                        comments_list= comments_raw
                    
                    #Import lyrics
                    if song_data.get('lyrics') is None or song_data.get('lyrics') == '':
                        missing_lyric_list.append(song_kuwo_id)
                        self.stdout.write(
                            self.style.WARNING(
                                f' - WARNING: Lyrics missing or empty for song ID: '
                                f'{song_kuwo_id}. Deleting folder.'
                            )
                        )
                        shutil.rmtree(song_folder_path)
                        self.stdout.write(
                            self.style.NOTICE(
                                f' - Successfully deleted folder for song ID: '
                                f'{song_kuwo_id} at {song_folder_path}'
                            )
                        )
                    else:
                        lyrics_content = str(song_data.get('lyrics', ''))

                    # --- Create or Update Song Object ---
                    # get_or_create tries to find an existing song
                    # by kuwo_id.
                    # If found, it returns the instance and 'created=False'.
                    # If not found,
                    # it creates a new instance using 'defaults' 
                    # and returns it, 'created=True'.
                    song_instance, created = Song.objects.get_or_create(
                        kuwo_id = song_kuwo_id,  # Unique identifier for lookup
                        defaults = {
                            # Map JSON keys to your Django model field names
                            'name': song_data.get('name', 'Unknown Song'),
                            'original_url': song_data.get(
                                'original_url',
                                f'https://star.kuwo.cn/star_index/'
                                f'{song_kuwo_id}.htm'
                            ),
                            'release_date': song_data.get(
                                'releasedate', ''
                            ),
                            'duration': song_data.get(
                                'duration', -1
                            ),
                            'album_name': song_data.get(
                                'album', ''
                            ),
                            'lyrics': lyrics_content,
                            'comments': comments_list,
                            'original_image_url': original_pic_url,
                        }
                    )

                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f' - Added song: {song_instance.name} '
                                f'(ID: {song_instance.kuwo_id})'
                            )
                        )
                    else:
                        # If the song already exists, update its fields.
                        self.stdout.write(
                            self.style.WARNING(
                                f' - Song already exists, updating: '
                                f'{song_instance.name} '
                                f'(ID: {song_instance.kuwo_id})'
                            )
                        )
                        # Update all relevant fields for existing songs
                        song_instance.name = song_data.get(
                            'name', 'Unknown Song'
                            )
                        song_instance.original_url = song_data.get(
                            'original_url',
                            f'https://star.kuwo.cn/star_index/'
                            f'{song_kuwo_id}.htm'
                        )
                        song_instance.release_date = song_data.get(
                            'releasedate', ''
                        )
                        song_instance.duration = song_data.get(
                            'duration', -1
                        )
                        song_instance.album_name = song_data.get(
                            'album', ''
                        )
                        song_instance.lyrics = lyrics_content
                        song_instance.comments = comments_list
                        song_instance.original_image_url = original_pic_url
                        
                        song_instance.singer = associated_singer

                        # Save the updates to the database
                        song_instance.save()  

                    if associated_singer:
                        self.stdout.write(self.style.SUCCESS(
                            f' - Linked song "{song_instance.name}"'
                            f' to singer: "{associated_singer.name}"'
                        ))
                    
                    # Define common image extensions to search for
                    possible_extensions: List[str] = [
                        '.jpg', '.png', '.jpeg', '.gif', '.webp'
                    ]
                    found_image_path: Optional[str] = None

                    # Iterate through possible extensions
                    # to find the local image file
                    for ext in possible_extensions:
                        current_local_image_path: str = os.path.join(
                            song_data_root, str(song_kuwo_id), f'pic{ext}'
                        )
                        if os.path.exists(current_local_image_path):
                            found_image_path = current_local_image_path
                            break  # Stop at the first found image

                    if found_image_path:
                        try:
                            # Construct the path relative to
                            # MEDIA_ROOT (or image_root)
                            # Ensure path separators are forward slashes
                            # for Django's ImageField
                            relative_path: str = os.path.relpath(
                                found_image_path, image_root
                            ).replace('\\', '/')
                            song_instance.image = relative_path
                            
                            # Only update the image field
                            # to optimize database write
                            song_instance.save(update_fields=['image'])
                            self.stdout.write(
                                ' - Associated song image: '
                                f'{song_instance.image}'
                                )
                            processed_images_count += 1

                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    ' - Failed to associate image'
                                    f' for song {song_instance.name} '
                                    f'({found_image_path}): {e}'
                                )
                            )
                            missing_images_count += 1
                    else:
                        # Log a warning if no local image is found
                        self.stdout.write(
                            self.style.WARNING(
                                f' - song {song_instance.name} '
                                'image file not found locally in any '
                                f'common format: '
                                f'{os.path.join(
                                    image_root,
                                    str(song_kuwo_id),
                                    "pic.*")}. '
                                f'Original URL: {original_pic_url}'
                            )
                        )
                        missing_images_count += 1

                    # Increment count for successfully processed songs
                    imported_songs_count += 1

                except json.JSONDecodeError:
                    # Handle cases 
                    # where the data.json file is corrupted or malformed
                    self.stdout.write(
                        self.style.ERROR(
                            ' - Could not parse JSON in '
                            f'{json_file_path}. Skipping.'
                            )
                    )
                except Exception as e:
                    # Catch any other unexpected errors
                    # during processing a single song
                    self.stdout.write(
                        self.style.ERROR(
                            ' - An unexpected error occurred processing '
                            f'{json_file_path}: {e}'
                            )
                    )

            # --- Final Summary ---
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n--- Data Import Summary ---'
                    )
                )
            self.stdout.write(
                self.style.SUCCESS(
                    'Total files processed: '
                    f'{total_files}'
                    )
                )
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully imported/updated songs: '
                    f'{imported_songs_count}'
                    )
                )
            self.stdout.write(
                self.style.SUCCESS(
                    'Images successfully associated: '
                    f'{processed_images_count}'
                    )
                )
            self.stdout.write(
                self.style.WARNING(
                    'songs with missing local images: '
                    f'{missing_images_count}'
                    )
                )
            
            if missing_lyric_list:
                self.stdout.write(
                    self.style.WARNING(
                        f'Songs with missing lyrics (IDs): {missing_lyric_list}'
                    )
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'--- Import Complete ---'
                    )
                )