from Y_Reader import Y_Reader
from Y_Searcher import filter_from_month, filter_recent_n_years
from utils import check_database, check_METADATA
check_database()
check_METADATA()

# keywords = '"causal discovery" OR "relation learning" OR "structure learning"'
keywords = '"residual learning"'
# filter_from_month(keywords, 2024, 1)
filter_recent_n_years(keywords, 10)
app = Y_Reader()
app.mainloop()