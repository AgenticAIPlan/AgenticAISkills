# License映射规范

## 映射表

| ID | 许可协议 | 关键词匹配 |
|----|----------|-----------|
| 1 | 公共领域 (CC0) | cc0, public domain |
| 2 | 署名 (CC BY 4.0) | cc-by-4.0, cc-by, cc by 4.0 |
| 3 | 署名-相同方式共享 (CC BY-SA 4.0) | cc-by-sa, cc by-sa |
| 4 | 署名-非商业性使用-相同方式共享 (CC BY-NC-SA 4.0) | cc-by-nc-sa, cc by-nc-sa |
| 5 | 署名-禁止演绎 (CC-BY-ND) | cc-by-nd, cc by-nd |
| 6 | 自由软件基金会 (GPL 2) | gpl-2, gpl2, gnu gpl |
| 7 | 署名-允许演绎 (ODC-BY) | odc-by, odc by |
| 8 | 其他 | 其他未匹配的协议 |

## 常见License映射示例

| 原始License | 映射ID |
|-------------|--------|
| cc-by-4.0 | 2 |
| mit | 8 |
| apache-2.0 | 8 |
| gpl-3.0 | 8 |
| bsd-3-clause | 8 |
| cc-by-sa-4.0 | 3 |
| cc0-1.0 | 1 |

## 自动映射逻辑

1. 将license字符串转为小写
2. 去除空格和特殊字符
3. 按关键词优先级匹配
4. 未匹配则默认为8（其他）
