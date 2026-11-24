from dags.utils.text_cleaner import clean_content


def test_news_content_cleaning():
    content = """
    삼성전자와 SK하이닉스가 23일 각각 3%와 1%대의 상승률을 보이며 정규장 거래를 마무리했다.

    전체 내용을 이해하기 위해서는 기사 본문과 함께 읽어야 합니다.
    구글 검색에서 기사를 우선적으로 보여줍니다.

    example@exm.co.kr
    """

    result = clean_content(content)

    assert "example@exm.co.kr" not in result
    assert "삼성전자와 SK하이닉스" in result