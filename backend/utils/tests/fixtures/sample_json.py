"""
Sample JSON data for testing
"""

# 简单PPT JSON
PPT_JSON_SIMPLE = {
    "title": "测试演示文稿",
    "sections": [
        {
            "id": "section1",
            "content": [
                {"type": "h1", "children": [{"text": "第一章"}]},
                {"type": "p", "children": [{"text": "这是第一章的内容"}]}
            ]
        }
    ],
    "references": []
}

# 完整PPT JSON
PPT_JSON_FULL = {
    "title": "完整演示文稿",
    "sections": [
        {
            "id": "section1",
            "content": [
                {"type": "h1", "children": [{"text": "第一章"}]},
                {"type": "bullets", "children": [
                    {"type": "bullet", "children": [
                        {"type": "h3", "children": [{"text": "要点1"}]},
                        {"type": "p", "children": [{"text": "详细内容1"}]}
                    ]},
                    {"type": "bullet", "children": [
                        {"type": "h3", "children": [{"text": "要点2"}]},
                        {"type": "p", "children": [{"text": "详细内容2"}]}
                    ]},
                    {"type": "bullet", "children": [
                        {"type": "h3", "children": [{"text": "要点3"}]},
                        {"type": "p", "children": [{"text": "详细内容3"}]}
                    ]}
                ]}
            ],
            "rootImage": {
                "url": "http://example.com/img.jpg",
                "alt": "测试图片",
                "background": False
            }
        },
        {
            "id": "section2",
            "content": [
                {"type": "h1", "children": [{"text": "第二章"}]},
                {"type": "p", "children": [{"text": "这是第二章的段落内容，内容会比较长一些"}]}
            ]
        }
    ],
    "references": [
        "参考文献1: 作者, 文章标题, 期刊名称, 2023",
        "参考文献2: 作者2, 书籍标题, 出版社, 2022",
        "参考文献3: 作者3, 论文标题, 会议名称, 2024"
    ]
}

# 带图片的PPT JSON
PPT_JSON_WITH_IMAGES = {
    "title": "带图片的演示",
    "sections": [
        {
            "id": "section1",
            "content": [
                {"type": "h1", "children": [{"text": "第一章"}]}
            ],
            "rootImage": {
                "url": "https://example.com/image1.jpg",
                "alt": "第一张图片",
                "background": False
            }
        },
        {
            "id": "section2",
            "content": [
                {"type": "h1", "children": [{"text": "第二章"}]}
            ],
            "rootImage": {
                "url": "https://example.com/image2.png",
                "alt": "第二张图片",
                "background": True
            }
        }
    ],
    "references": []
}

# 只有段落的PPT JSON
PPT_JSON_ONLY_PARAGRAPHS = {
    "title": "只有段落",
    "sections": [
        {
            "id": "section1",
            "content": [
                {"type": "h1", "children": [{"text": "标题"}]},
                {"type": "p", "children": [{"text": "第一段内容"}]},
                {"type": "p", "children": [{"text": "第二段内容"}]}
            ]
        }
    ],
    "references": []
}

# 长内容的PPT JSON
PPT_JSON_LONG_CONTENT = {
    "title": "长内容测试",
    "sections": [
        {
            "id": "section1",
            "content": [
                {"type": "h1", "children": [{"text": "长内容章节"}]},
                {"type": "p", "children": [{"text": "这是一段很长的内容。" * 50}]}
            ]
        }
    ],
    "references": []
}

# 无效的PPT JSON
PPT_JSON_INVALID = {
    "sections": "invalid",  # 应该是列表
}

# 空PPT JSON
PPT_JSON_EMPTY = {
    "title": "",
    "sections": [],
    "references": []
}
