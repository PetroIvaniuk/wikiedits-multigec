import dateparser
import requests
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Tag


def _update_date_column(df, date_col_in, date_col_out):
    """
    Return the same dataset with additional column `date`
    that was created based on `date_wiki` by converting wiki format into standard date format
    """
    # for czech language define date format according wiki dateformat
    df[date_col_out] = pd.to_datetime(df[date_col_in], errors='coerce', format='%d. %m. %Y')
    # for other languages use dateparser library
    df[date_col_out] = df.apply(
        lambda x: pd.to_datetime(dateparser.parse(x[date_col_in], languages=[x['lang_code']]))
            if pd.isnull(x[date_col_out]) else x[date_col_out], axis=1
    )
    df[date_col_out] = df[date_col_out].apply(lambda x: str(x.date()) if x is not None else x)


def get_edit_pages_metadata(url, metadata_init):
    """
    Return metadata about all pages with edits
    """
    content = BeautifulSoup(requests.get(url).content, features="html.parser")
    _obj = content.find_all("h4")

    metadata = []
    for h_obj in _obj[:]:
        ul_obj = h_obj.find_next("ul", {"class": "special"})

        for li_obj in ul_obj.find_all("li"):
            if li_obj.find("a", {"class": "mw-userlink"}) is not None:
                author = li_obj.find("a", {"class": "mw-userlink"}).get_text()
            else:
                author = None

            span_obj = li_obj.find("span", {"class": "mw-changeslist-line-inner"})
            title_obj = span_obj.find("span", {"class": "mw-title"})
            tag_obj = span_obj.find("span", {"class": "mw-tag-markers"})

            dict_ = {**{"date_edit_wiki": h_obj.get_text()}, **metadata_init}
            links_obj = span_obj.find("span", {"class": "mw-changeslist-links"})

            if len(links_obj) == 2:
                for i in links_obj:
                    # take data if only first diff object has a link
                    if list(links_obj)[0].find("a") is not None:
                        dict_[i.get_text()] = i.find("a")["href"]

                dict_["title"] = title_obj.get_text()
                dict_["url"] = title_obj.find("a")["href"]
                dict_["author"] = author
                dict_["tags"] = [i.get_text() for i in tag_obj.find_all("span")]
            metadata.append(dict_)
    return metadata