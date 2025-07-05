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

        name_match_ids = set()
        info_match_ids = set()
        singer_name_match_ids = set()
        lyrics_match_ids = set()

        if query:
            start_time = time.time()

            if search_type == 'song':
                # Filter singer by query
                name_match = Song.objects.filter(name__icontains=query)
                singer_name_match = Song.objects.filter(singer__name__icontains=query)
                lyrics_match = Song.objects.filter(lyrics__icontains=query)

                name_match_ids = set(name_match.values_list('pk', flat=True))
                singer_name_match_ids = set(singer_name_match.values_list('pk', flat=True))
                lyrics_match_ids = set(lyrics_match.values_list('pk', flat=True))
                
                if name_match.exists():
                    results.append({'separator': "name"})
                    results.extend(list(name_match))
                    
                distinct_singer_name_match = singer_name_match.exclude(pk__in=name_match_ids)
                
                if distinct_singer_name_match.exists():
                    results.append({'separator': "singer_name"})
                    results.extend(list(distinct_singer_name_match))
                    
                distinct_lyrics_match = lyrics_match.\
                        exclude(pk__in=name_match_ids).\
                        exclude(pk__in=singer_name_match_ids)
                        
                if distinct_lyrics_match.exists():
                    results.append({'separator': "lyric"})
                    results.extend(list(lyrics_match))
                    
                result_count = name_match.count() + singer_name_match.count() + lyrics_match.count()


            elif search_type == 'singer':
                # Filter singer by query
                name_match = Singer.objects.filter(name__icontains=query)
                info_match = Singer.objects.filter(info__icontains=query)

                name_match_ids = set(name_match.values_list('pk', flat=True))
                info_match_ids = set(info_match.values_list('pk', flat=True))
                
                if name_match.exists():
                    results.append({'separator': "name"})
                    results.extend(list(name_match))
                    
                distinct_info_match = info_match.exclude(pk__in=name_match_ids)

                if distinct_info_match.exists():
                    results.append({'separator': "info"})
                    results.extend(list(distinct_info_match))
                
                result_count = name_match.count() + distinct_info_match.count()

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