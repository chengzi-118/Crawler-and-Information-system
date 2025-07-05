from django.shortcuts import render
from django.views import View
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import time

from song.models import Song
from singer.models import Singer

class SearchResultsView(View):
    template_name = 'search/search_results.html'
    paginate_by = 18

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        search_type = kwargs.get('search_type', request.GET.get('type', 'song'))

        page_number = request.GET.get('page', 1)

        results = []
        result_count = 0
        search_time = 0.0

        # These sets are used to track IDs for display count and exclusion in subsequent queries.
        # They reflect the initial broad matches for each category.
        name_match_ids_overall = set() # Accumulates all distinct IDs added to 'results'
        info_match_ids_overall = set() # For singer search
        
        # Track IDs specifically for initial query results for correct exclusion
        initial_song_name_ids = set()
        initial_singer_name_ids = set()
        initial_lyrics_ids = set()
        initial_singer_info_ids = set()


        if query:
            start_time = time.time()

            if search_type == 'song':
                # Filter singer by query
                name_match = Song.objects.filter(name__icontains=query)
                singer_name_match = Song.objects.filter(singer__name__icontains=query)
                lyrics_match = Song.objects.filter(lyrics__icontains=query)

                initial_song_name_ids = set(name_match.values_list('pk', flat=True))
                initial_singer_name_ids = set(singer_name_match.values_list('pk', flat=True))
                initial_lyrics_ids = set(lyrics_match.values_list('pk', flat=True))
                
                if name_match.exists():
                    results.append({'separator': "name"})
                    for song in name_match:
                        # Ensure PK is valid and not already added from a previous iteration if any
                        if song.pk is not None and song.pk != '' and song.pk not in name_match_ids_overall:
                            results.append(song)
                            name_match_ids_overall.add(song.pk)
                    
                distinct_singer_name_match = singer_name_match.exclude(pk__in=name_match_ids_overall)
                
                if distinct_singer_name_match.exists():
                    results.append({'separator': "singer_name"})
                    for song in distinct_singer_name_match:
                        # Ensure PK is valid and not already added
                        if song.pk is not None and song.pk != '' and song.pk not in name_match_ids_overall:
                            results.append(song)
                            name_match_ids_overall.add(song.pk)
                    
                # Use the accumulated IDs from both name and singer name matches for lyrics exclusion
                ids_for_lyrics_exclusion = name_match_ids_overall.union(initial_song_name_ids).union(initial_singer_name_ids) # More robust exclusion set
                distinct_lyrics_match = lyrics_match.\
                        exclude(pk__in=ids_for_lyrics_exclusion)
                        
                if distinct_lyrics_match.exists():
                    results.append({'separator': "lyric"})
                    for song in distinct_lyrics_match:
                        # Ensure PK is valid and not already added
                        if song.pk is not None and song.pk != '' and song.pk not in name_match_ids_overall:
                            results.append(song)
                            name_match_ids_overall.add(song.pk)
                            
                result_count = len(name_match_ids_overall)


            elif search_type == 'singer':
                # Filter singer by query
                name_match = Singer.objects.filter(name__icontains=query)
                info_match = Singer.objects.filter(info__icontains=query)

                # Initialize a single set to track all distinct singer IDs added
                current_added_singer_ids = set() 
                
                if name_match.exists():
                    results.append({'separator': "name"})
                    for singer in name_match:
                        # Ensure PK is valid and not already added
                        if singer.pk is not None and singer.pk != '' and singer.pk not in current_added_singer_ids:
                            results.append(singer)
                            current_added_singer_ids.add(singer.pk)
                    
                distinct_info_match = info_match.exclude(pk__in=current_added_singer_ids)

                if distinct_info_match.exists():
                    results.append({'separator': "info"})
                    for singer in distinct_info_match:
                        # Ensure PK is valid and not already added
                        if singer.pk is not None and singer.pk != '' and singer.pk not in current_added_singer_ids:
                            results.append(singer)
                            current_added_singer_ids.add(singer.pk)
                
                result_count = len(current_added_singer_ids)

            end_time = time.time()
            search_time = round((end_time - start_time) * 1000, 2)

        paginator = Paginator(results, self.paginate_by)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        is_paginated = page_obj.has_other_pages()

        context = {
            'query': query,
            'search_type': search_type,
            'results': page_obj.object_list,
            'result_count': result_count,
            'search_time': search_time,
            'page_obj': page_obj,
            'is_paginated': is_paginated,
            'request': request,
        }
        return render(request, self.template_name, context)

class SearchPageView(View):
    template_name = 'search/search_page.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)