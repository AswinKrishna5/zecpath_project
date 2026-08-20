from rest_framework.pagination import PageNumberPagination

class CandidatePagination(PageNumberPagination):

    page_size=5
    page_size_query_param="page_size"
    max_page_size=20

class JobPagination(PageNumberPagination):
    page_size=5
    page_size_query_param="page_size"
    max_page_size=20