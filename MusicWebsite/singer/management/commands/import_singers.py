import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from typing import Any, Dict, List, Optional
from argparse import ArgumentParser
from ...models import Singer


class Command(BaseCommand):
    """
    Django management command to import scraped singer data into the database.

    This command expects a root directory
    containing subfolders named by singer ID,
    each holding a 'data.json' file with singer metadata
    and an image file (e.g., 'pic.jpg').
    """
    # The 'help' attribute is the short description shown
    # when running 'python manage.py help import_data'
    help = (
        'Imports scraped singer data from individual data.json files '
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
            'singer_data_root',
            type=str,
            help=(
                'The root directory containing singer ID folders '
                '(e.g., D:\\code\\python\\BigHomework\\Singer)'
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
        2. Discovers all 'data.json' files within the singer data root.
        3. Imports or updates singer data in a database transaction.
        4. Associates local image files with singer records.
        5. Provides detailed progress and summary messages to the console.

        Args:
            *args (Any): Positional arguments passed to the command.
            **options (Any): Keyword arguments (from add_arguments)
            passed to the command.
        """
        singer_data_root: str = options['singer_data_root']
        image_root: str = options['image_root']

        # If --image_root is not provided,
        # assume it's the same as singer_data_root
        if not image_root:
            image_root = singer_data_root

        # --- Input Validation ---
        if not os.path.isdir(singer_data_root):
            raise CommandError(
                self.style.ERROR(
                    f'Error: Singer data root directory does not exist '
                    f'or is not a directory: {singer_data_root}'
                )
            )

        # Display initial search message
        self.stdout.write(
            self.style.SUCCESS(
                f'Searching for data.json files in {singer_data_root}...'
                )
        )

        json_files_to_process: List[str] = []

        # --- File Discovery ---
        # os.walk traverses the directory tree (root, subdirectories, files)
        for root, _, files in os.walk(singer_data_root):
            # Check if 'data.json' exists in the current directory
            if 'data.json' in files:
                json_files_to_process.append(os.path.join(root, 'data.json'))

        if not json_files_to_process:
            raise CommandError(
                self.style.ERROR(
                    f'Error: No data.json files found in {singer_data_root} '
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
        imported_singers_count: int = 0
        processed_images_count: int = 0
        missing_images_count: int = 0

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

                try:
                    # Extract singer ID from the folder name
                    singer_id_from_path: str = os.path.basename(
                        os.path.dirname(json_file_path)
                    )
                    # Convert the string ID to an integer,
                    # as kuwo_id is an IntegerField
                    singer_kuwo_id: int = int(singer_id_from_path)

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
                    # Open and load the JSON data for the current singer
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        singer_data: Dict[str, Any] = json.load(f)
                                                                               
                    # Validate if the ID in JSON matches the folder ID
                    if singer_data.get('id') != singer_kuwo_id:
                        self.stdout.write(
                            self.style.WARNING(
                                f' - ID mismatch for {json_file_path}'
                                f': Folder ID '
                                f'{singer_kuwo_id} vs JSON ID '
                                f'{singer_data.get("id")}. '
                                f'Using folder ID for consistency.'
                            )
                        )
                        # Correct the data to match the folder
                        # for consistency if needed
                        singer_data['id'] = singer_kuwo_id

                    original_pic_url: str = singer_data.get('pic', '')

                    # --- Create or Update Singer Object ---
                    # get_or_create tries to find an existing singer
                    # by kuwo_id.
                    # If found, it returns the instance and 'created=False'.
                    # If not found,
                    # it creates a new instance using 'defaults' 
                    # and returns it, 'created=True'.
                    singer_instance, created = Singer.objects.get_or_create(
                        kuwo_id = singer_kuwo_id,  # Unique identifier for lookup
                        defaults= {
                            # Map JSON keys to your Django model field names
                            'name': singer_data.get('name', 'Unknown Singer'),
                            'info': singer_data.get('info', ''),
                            'original_url': singer_data.get(
                                'original_url',
                                f'https://star.kuwo.cn/star_index/'
                                f'{singer_kuwo_id}.htm'
                            ),
                            'alias': singer_data.get('aartist', ''),
                            'fan_num': singer_data.get('artistFans', 0),
                            'album_num': singer_data.get('albumNum', 0),
                            'mv_num': singer_data.get('mvNum', 0),
                            'music_num': singer_data.get('musicNum', 0),
                            'birthday': singer_data.get('birthday', ''),
                            'birthplace': singer_data.get('birthplace', ''),
                            'region': singer_data.get('region', ''),
                            'gender': singer_data.get('gender', ''),
                            'weight': singer_data.get('weight', ''),
                            'height': singer_data.get('height', ''),
                            'language': singer_data.get('language', ''),
                            'constellation': singer_data.get(
                                'constellation', ''
                                ),
                            'original_image_url': original_pic_url,
                        }
                    )

                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f' - Added singer: {singer_instance.name} '
                                f'(ID: {singer_instance.kuwo_id})'
                            )
                        )
                    else:
                        # If the singer already exists, update its fields.
                        self.stdout.write(
                            self.style.WARNING(
                                f' - Singer already exists, updating: '
                                f'{singer_instance.name} '
                                f'(ID: {singer_instance.kuwo_id})'
                            )
                        )
                        # Update all relevant fields for existing singers
                        singer_instance.name = singer_data.get(
                            'name', 'Unknown Singer'
                            )
                        singer_instance.info = singer_data.get('info', '')
                        singer_instance.original_url = singer_data.get(
                            'original_url',
                            f'https://star.kuwo.cn/star_index/'
                            f'{singer_kuwo_id}.htm'
                        )
                        singer_instance.alias = singer_data.\
                            get('aartist', '')
                        singer_instance.fan_num = singer_data.\
                            get('artistFans', 0)
                        singer_instance.album_num = singer_data.\
                            get('albumNum', 0)
                        singer_instance.mv_num = singer_data.\
                            get('mvNum', 0)
                        singer_instance.music_num = singer_data.\
                            get('musicNum', 0)
                        singer_instance.birthday = singer_data.\
                            get('birthday', '')
                        singer_instance.birthplace = singer_data\
                            .get('birthplace', '')
                        singer_instance.region = singer_data.\
                            get('region', '')
                        singer_instance.gender = singer_data.\
                            get('gender', '')
                        singer_instance.weight = singer_data.\
                            get('weight', '')
                        singer_instance.height = singer_data.\
                            get('height', '')
                        singer_instance.language = singer_data\
                            .get('language', '')
                        singer_instance.constellation = singer_data\
                            .get('constellation', '')
                        singer_instance.original_image_url = original_pic_url
                        # Save the updates to the database
                        singer_instance.save()  

                    # Define common image extensions to search for
                    possible_extensions: List[str] = [
                        '.jpg', '.png', '.jpeg', '.gif', '.webp'
                    ]
                    found_image_path: Optional[str] = None

                    # Iterate through possible extensions
                    # to find the local image file
                    for ext in possible_extensions:
                        current_local_image_path: str = os.path.join(
                            singer_data_root, str(singer_kuwo_id), f'pic{ext}'
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
                            singer_instance.image = relative_path
                            
                            # Only update the image field
                            # to optimize database write
                            singer_instance.save(update_fields=['image'])
                            self.stdout.write(
                                ' - Associated singer image: '
                                f'{singer_instance.image}'
                                )
                            processed_images_count += 1

                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    ' - Failed to associate image'
                                    f' for singer {singer_instance.name} '
                                    f'({found_image_path}): {e}'
                                )
                            )
                            missing_images_count += 1
                    else:
                        # Log a warning if no local image is found
                        self.stdout.write(
                            self.style.WARNING(
                                f' - Singer {singer_instance.name} '
                                'image file not found locally in any '
                                f'common format: '
                                f'{os.path.join(
                                    image_root,
                                    str(singer_kuwo_id),
                                    "pic.*")}. '
                                f'Original URL: {original_pic_url}'
                            )
                        )
                        missing_images_count += 1

                    # Increment count for successfully processed singers
                    imported_singers_count += 1

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
                    # during processing a single singer
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
                    'Successfully imported/updated singers: '
                    f'{imported_singers_count}'
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
                    'Singers with missing local images: '
                    f'{missing_images_count}'
                    )
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'--- Import Complete ---'
                    )
                )