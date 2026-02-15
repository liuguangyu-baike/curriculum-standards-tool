# 目标
把 "DCI Arrangements of NGSS.pdf"、"Appendix F Science and Engineering Practices.pdf"文件，转换成方便查询的网站

# 当前文件格式介绍
文件5-103页，遵循相同的格式。整体为一个表格
1. 最上面格子为Perfomance Expectation预期表现，为每个学段学生要达到的目标
2. 下方为并列三个格子
    1. 最左侧Science and Engineering Practice为科学与工程探究能力要求，简称SEP
    2. 中间Disciplinary Core Ideas为领域核心知识，简称DCI
    3. 右侧Crosscutting Concept为科学思维，简称CCC

# 编码规则
1. 预期表现部分：[学段]-[领域][核心概念序号]-[标准序号]
    - 例如：K-PS2-1，表示幼儿园（Kindergarten）学段，物质科学领域，第2个核心概念的第1条学业标准
2. DCI部分：[领域][核心概念序号].[子概念序号]-[学段]-[要点序号]
    - 例如：PS2.A-K-1，表示物质科学领域，第2个核心概念，第A个子概念，幼儿园阶段的第1条内容。要点序号从1开始顺序编号
3. 学段部分编码：
    - K：Kindergarten，幼儿园
    - 1-5：分别对应1-5年级
    - MS：初中
    - HS：高中
4. 领域部分编码：
    - PS：物质科学
    - LS：生命科学
    - ESS：地球与空间科学

# 预期功能
1. 支持按照年级（多选）、领域（多选），列出对应的文件内容。可选查询项包括：
    - PE
    - DCI
    - SEP
    - CCC
2. （mvp暂不做）AI基于查询结果进行总结。例如查询了3、4、5年级物质科学的DCI，AI总结3-5年级作为一个学段整体的知识目标
3. （mvp暂不做）支持按年级分组（例如K-2、3-5、MS、HS），AI总结各组的DCI、SEP、CCC、PE

# 数据结构建议
（以下仅为建议，如果不合适可以与我商量修改）
DCI、PE、SEP、CCC各一张表，未来也可能加入基于中国课标的表。各个表通过领域、学段相关联

## DCI
1. 建议以DCI编码（[DCI前缀]-[领域][核心概念序号].[子概念序号]-[学段]-[要点序号]）作为id
2. 每一个条目下需要记录：
    1. 领域
    2. 核心概念序号
    3. 核心概念序号对应的内容
    4. 子概念序号
    5. 子概念序号对应的内容
    6. 要点内容
    7. 学段
    8. 关联PE（在每一条后的括号中）

## PE
1. 建议以PE编码（[PE前缀]-[学段]-[领域][核心概念序号]-[标准序号]）作为id
2. 每一个条目下需要记录：
    1. 学段
    2. 领域
    3. 核心概念序号
    4. 核心概念序号对应的内容
    5. 标准序号
    6. 标准序号对应的内容
    7. 说明（每一条后clarification statement的内容）
    8. 评价范围（assessment boundary的内容，如有）

## CCC
1. 每一个条目需要记录：
    1. 跨学科概念编号
    2. 跨学科概念内容
    3. 要点内容
    4. 学段
    5. 关联PE
2. 跨学科概念一共7个，编号与内容的对应关系为：
    1. 模式（patterns）
    2. 因果关系
    3. 尺度、比例和数量
    4. 系统与系统模型
    5. 能量与物质
    6. 结构与功能
    7. 稳定与变化
3. 要点内容需要去重，相同要点只记录一次
4. 一条要点内容可以对应多个学段、多个关联PE

## SEP
从"Appedix F Science and Engineering Practices.pdf文件中17-32页的表格中提取"
1. 每条SEP id编码方式为：[SEP前缀]-[Practice序号]-[学段]-[类目序号]-[项目序号]
    - 例如：SEP-1-K_2-1-1表示：
        - Practice 1: Asking Questions and Defining Problems
        - 学段：K-2
        - 第1个类目：该Practice、该学段下，带有bulletpoint的表格的第1行）
        - 第1个项目：所属类目单元格中，第1个bulletpoint
    - 内容为：Ask questions based on observations to find more information about the natural and/or designed world(s).
2. 每个SEP条目需要记录：
    1. Practice序号
    2. Practice英文名称
    3. Practice中文名称
    4. 学段："K-2","3-5","6-8","9-12"
    5. 学段目标：表头下的第1行（不带bulletpoint）
    6. 类目序号
    7. 项目序号
    8. 项目内容
3. SEP一共有8个，编号与内容的对应关系为：
    1. Asking Questions and Defining Problems
    2. Developing and using models
    3. Planning and carrying out investigations
    4. Analyzing and interpreting data
    5. Using mathematics and computational thinking
    6. Constructing explanations and designing solutions
    7. Engaging in argument from evidence
    8. Obtaining, evaluating, and communicating information