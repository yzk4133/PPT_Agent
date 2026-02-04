"""
Sample XML data for testing
"""

# 简单幻灯片XML
SLIDE_SIMPLE = '<SECTION layout="vertical"><H1>标题</H1><P>内容</P></SECTION>'

# 带项目列表的XML
SLIDE_WITH_BULLETS = '''<SECTION layout="vertical">
    <H1>要点列表</H1>
    <BULLETS>
        <P>要点一</P>
        <P>要点二</P>
        <P>要点三</P>
        <P>要点四</P>
    </BULLETS>
</SECTION>'''

# 带图片的XML
SLIDE_WITH_IMAGE = '''<SECTION layout="vertical">
    <H1>图片页</H1>
    <IMG src="http://example.com/img.jpg"/>
    <IMG src="https://example.com/img2.png"/>
</SECTION>'''

# 带分栏的XML
SLIDE_WITH_COLUMNS = '''<SECTION layout="vertical">
    <H1>分栏内容</H1>
    <COLUMNS>
        <P>第一列内容</P>
        <P>第二列内容</P>
    </COLUMNS>
</SECTION>'''

# 带H3子标题的XML
SLIDE_WITH_H3 = '''<SECTION layout="vertical">
    <H1>主标题</H1>
    <H3>子标题1</H3>
    <H3>子标题2</H3>
    <P>段落内容</P>
</SECTION>'''

# 空XML
SLIDE_EMPTY = '<SECTION layout="vertical"></SECTION>'

# 没有标题的XML
SLIDE_NO_TITLE = '<SECTION layout="vertical"><P>只有内容没有标题</P></SECTION>'

# 复杂XML（多种元素）
SLIDE_COMPLEX = '''<SECTION layout="horizontal">
    <H1>复杂页面</H1>
    <BULLETS>
        <P>要点1</P>
        <P>要点2</P>
    </BULLETS>
    <IMG src="http://example.com/complex.jpg"/>
    <H3>子标题</H3>
    <P>段落内容</P>
</SECTION>'''

# 中文内容XML
SLIDE_CHINESE = '''<SECTION layout="vertical">
    <H1>人工智能技术</H1>
    <P>人工智能是计算机科学的一个分支</P>
    <BULLETS>
        <P>机器学习</P>
        <P>深度学习</P>
        <P>自然语言处理</P>
    </BULLETS>
</SECTION>'''
