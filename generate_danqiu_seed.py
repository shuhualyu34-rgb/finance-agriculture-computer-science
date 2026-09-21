#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丹邱丝苗米平台模拟数据生成脚本
输出：可直接在 MySQL 8.0 执行的 danqiu_rice_seed.sql
"""

import random
import uuid
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# 固定随机种子，保证可复现
random.seed(42)

# 输出路径
OUTPUT_DIR = Path(__file__).parent
OUTPUT_SQL = OUTPUT_DIR / "danqiu_rice_seed.sql"

# 数据规模配置
# 目标：200 户、2500 亩、亩成本 600-700 元
SCALE = {
    "farmers": 200,
    "consumers": 80,
    "admin_users": 8,  # 银行、保险、运营、政府、平台管理员
    "plots_per_farmer_min": 1,
    "plots_per_farmer_max": 3,
    "target_total_area_mu": 2500.0,
    "seasons": 4,
    "records_per_plot_season_min": 2,
    "records_per_plot_season_max": 4,
    "attachment_rate": 0.5,
    "standard_versions": 3,
    "clauses_per_version": 10,
    "certifications": 150,
    "inspections": 80,
    "reports": 12,
    "policies": 220,
    "claims": 30,
    "loans": 150,
    "trace_codes": 320,
    "adoptions": 60,
    "orders": 1000,
}

# 时间范围
BASE_DATE = datetime(2024, 3, 1)
END_DATE = datetime(2026, 8, 31)

# 数据字典
VILLAGES = ["丹邱村", "丹邱一村", "丹邱二村", "丹邱新村"]

# 姓名池，程序组合生成足够数量
FARMER_SURNAMES = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴",
                   "孙", "郑", "谢", "罗", "高", "林", "何", "梁", "曾", "潘",
                   "邓", "冯", "蔡", "彭", "杜", "蒋", "范", "钟", "卢", "叶",
                   "董", "田", "袁", "于", "余", "魏", "许", "马", "朱", "胡"]
FARMER_GIVEN_NAMES = ["伟", "强", "芳", "洋", "明", "秀芬", "建国", "丽华", "志刚", "桂花",
                      "大伟", "敏", "国华", "秀英", "建军", "远", "丹", "平", "红梅", "伟民",
                      "秀丽", "强", "国庆", "晓燕", "伟民", "娟", "志豪", "丽娟", "伟", "桂花",
                      "志强", "淑英", "国华", "秀兰", "建华", "建平", "秀英", "玉梅", "永强", "淑华"]

CONSUMER_SURNAMES = ["林", "郑", "黄", "陈", "李", "王", "张", "刘", "赵", "孙",
                     "周", "吴", "徐", "朱", "马", "胡", "郭", "何", "高", "罗"]
CONSUMER_GIVEN_NAMES = ["小明", "晓燕", "伟", "静", "磊", "璐", "涛", "芳", "敏", "强",
                        "婷", "刚", "佳", "敏", "杰", "丽", "超", "艳", "勇", "军",
                        "洋", "娟", "艳", "涛", "明", "玲", "平", "霞", "辉", "静",
                        "欣", "宇", "婷", "俊", "慧", "强", "磊", "洋", "敏", "洁"]


def make_unique_names(surnames, given_names, count):
    names = []
    seen = set()
    while len(names) < count:
        name = random.choice(surnames) + random.choice(given_names)
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


FARMER_NAMES = make_unique_names(FARMER_SURNAMES, FARMER_GIVEN_NAMES, SCALE["farmers"])
CONSUMER_NAMES = make_unique_names(CONSUMER_SURNAMES, CONSUMER_GIVEN_NAMES, SCALE["consumers"])

ADMIN_USERS = [
    ("bank_01", "农行审批员", "BANK"),
    ("bank_02", "农商行审批员", "BANK"),
    ("insurance_01", "人保核保员", "INSURANCE"),
    ("operator_01", "品牌运营专员", "OPERATOR"),
    ("operator_02", "平台运营主管", "OPERATOR"),
    ("gov_01", "农业局监管员", "GOVERNMENT"),
    ("gov_02", "乡镇农技员", "GOVERNMENT"),
    ("admin_01", "平台管理员", "ADMIN"),
]

RECORD_TYPES = ["SOWING", "FERTILIZING", "PESTICIDE", "IRRIGATION", "HARVEST", "QUALITY_TEST"]
RECORD_TYPE_WEIGHTS = [15, 30, 20, 20, 10, 5]

STAGES = ["PLANTING", "PROCESSING", "QUALITY", "GRADING", "PACKAGING", "DISTRIBUTION"]

STANDARD_CLAUSE_TEMPLATES = [
    ("PLANTING", "PLT-{:02d}", "土壤墒情管理", "土壤含水量保持在适宜范围，定期进行墒情监测。"),
    ("PLANTING", "PLT-{:02d}", "种子质量要求", "使用经检疫合格、发芽率达到标准的优质种子。"),
    ("PROCESSING", "PRC-{:02d}", "收割作业规范", "采用机械化收割，控制留茬高度，减少谷粒损失。"),
    ("PROCESSING", "PRC-{:02d}", "烘干工艺控制", "稻谷烘干温度控制在40℃以下，水分降至14.5%以下。"),
    ("QUALITY", "QLT-{:02d}", "农药残留检测", "每批次产品农药残留指标须符合国家绿色食品标准。"),
    ("QUALITY", "QLT-{:02d}", "重金属检测", "镉、铅、砷等重金属含量不得超过国家标准限值。"),
    ("GRADING", "GRD-{:02d}", "外观分级", "按米粒完整度、垩白度、色泽等指标进行特级/一级/二级分级。"),
    ("GRADING", "GRD-{:02d}", "食味品质", "食味值不低于80分，直链淀粉含量符合优质丝苗米范围。"),
    ("PACKAGING", "PKG-{:02d}", "包装标识", "包装须标明产地、等级、净含量、生产日期、执行标准。"),
    ("DISTRIBUTION", "DIS-{:02d}", "冷链储运", "运输过程保持干燥通风，防止霉变和交叉污染。"),
]

CARRIERS = ["顺丰速运", "京东物流", "中通快递", "圆通速递", "丹邱自营物流"]

# ID / 编码生成器
id_counters = defaultdict(int)


def next_id(table: str) -> int:
    id_counters[table] += 1
    return id_counters[table]


def next_code(prefix: str, date: datetime = None) -> str:
    id_counters[prefix] += 1
    if date:
        return f"{prefix}{date.strftime('%Y%m%d')}{id_counters[prefix]:04d}"
    return f"{prefix}{id_counters[prefix]:04d}"


def next_year_code(prefix: str, year: int) -> str:
    id_counters[prefix] += 1
    return f"{prefix}{year}{id_counters[prefix]:04d}"


def rand_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def rand_time_str(d: datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")


def rand_date_str(d: datetime = None) -> str:
    if d is None:
        d = rand_date(BASE_DATE, END_DATE)
    return d.strftime("%Y-%m-%d")


def sql_str(s) -> str:
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def sql_json(obj) -> str:
    if obj is None:
        return "NULL"
    return sql_str(json.dumps(obj, ensure_ascii=False))


def sql_bool(b) -> str:
    if b is None:
        return "NULL"
    return "1" if b else "0"


def insert_sql(table: str, columns: list, rows: list) -> str:
    if not rows:
        return ""
    header = f"INSERT INTO `{table}` ({', '.join([f'`{c}`' for c in columns])}) VALUES\n"
    values = ",\n".join(["  (" + ", ".join(map(str, row)) + ")" for row in rows])
    return header + values + ";\n\n"


def gen_users():
    users = []
    user_roles = []
    farmers = []
    consumers = []
    admins = []

    # 农户
    for i, name in enumerate(FARMER_NAMES[:SCALE["farmers"]], 1):
        uid = next_id("sys_user")
        username = f"farmer_{i:03d}"
        phone = f"138{i:04d}{random.randint(1000, 9999)}"
        users.append((uid, username, None, name, phone, "ACTIVE"))
        user_roles.append((uid, "FARMER"))
        farmers.append(uid)

    # 消费者
    for i, name in enumerate(CONSUMER_NAMES[:SCALE["consumers"]], 1):
        uid = next_id("sys_user")
        username = f"consumer_{i:03d}"
        phone = f"139{i:04d}{random.randint(1000, 9999)}"
        users.append((uid, username, None, name, phone, "ACTIVE"))
        user_roles.append((uid, "CONSUMER"))
        consumers.append(uid)

    # 管理员/机构用户
    for username, real_name, role in ADMIN_USERS[:SCALE["admin_users"]]:
        uid = next_id("sys_user")
        phone = f"137{random.randint(10000000, 99999999)}"
        users.append((uid, username, None, real_name, phone, "ACTIVE"))
        user_roles.append((uid, role))
        admins.append((uid, role))

    return users, user_roles, farmers, consumers, admins


def gen_farmer_profiles(farmers):
    profiles = []
    for i, uid in enumerate(farmers, 1):
        village = random.choice(VILLAGES)
        address = f"{village}第{i}组"
        id_card = f"440183{random.randint(19600101, 20051231)}{random.randint(1000, 9999)}"
        status = random.choices(
            ["PENDING", "CERTIFIED", "REJECTED", "SUSPENDED"],
            weights=[2, 6, 1, 1]
        )[0]
        cert_at = rand_time_str(rand_date(BASE_DATE, datetime(2026, 6, 1))) if status == "CERTIFIED" else None
        profiles.append((i, uid, village, address, id_card, status, cert_at))
    return profiles


def gen_plots(farmers, profiles):
    plots = []
    plot_id_to_farmer = {}
    raw_areas = []

    # 第一步：生成地块结构并分配随机比例
    for farmer_idx, farmer_id in enumerate(farmers, 1):
        village = profiles[farmer_idx - 1][2]
        n = random.randint(SCALE["plots_per_farmer_min"], SCALE["plots_per_farmer_max"])
        for j in range(n):
            pid = next_id("farm_plot")
            plot_code = f"DK{random.choice(['2024','2025'])}{pid:04d}"
            plot_name = f"{village}{pid:03d}号田"
            # 随机比例面积，后续缩放至 2500 亩
            raw_area = random.uniform(3.0, 25.0)
            lon = round(random.uniform(113.6, 113.9), 7)
            lat = round(random.uniform(23.2, 23.4), 7)
            boundary = {
                "type": "Polygon",
                "coordinates": [[
                    [lon, lat],
                    [lon + 0.001, lat],
                    [lon + 0.001, lat + 0.001],
                    [lon, lat + 0.001],
                    [lon, lat]
                ]]
            }
            image_url = f"https://danqiu.example.com/satellite/{plot_code}.jpg"
            raw_areas.append(raw_area)
            plots.append({
                "pid": pid,
                "plot_code": plot_code,
                "farmer_id": farmer_id,
                "plot_name": plot_name,
                "village": village,
                "lon": lon,
                "lat": lat,
                "boundary": boundary,
                "image_url": image_url,
            })
            plot_id_to_farmer[pid] = farmer_id

    # 第二步：按比例缩放，使总面积 ≈ 2500 亩
    total_raw = sum(raw_areas)
    target = SCALE["target_total_area_mu"]
    scale_factor = target / total_raw
    for i, plot in enumerate(plots):
        scaled = round(raw_areas[i] * scale_factor, 2)
        if scaled < 0.5:
            scaled = 0.5
        plot["area"] = scaled

    # 第三步：转换为元组
    result = []
    for p in plots:
        result.append((
            p["pid"], p["plot_code"], p["farmer_id"], p["plot_name"], p["village"],
            p["area"], "增科新选丝苗1号", p["lon"], p["lat"], p["boundary"],
            p["image_url"], "ACTIVE"
        ))
    return result, plot_id_to_farmer


def gen_seasons():
    seasons = []
    data = [
        ("S2024A", "2024年早稻", "2024-03-15", "2024-07-20", "CLOSED"),
        ("S2024B", "2024年晚稻", "2024-07-25", "2024-11-10", "CLOSED"),
        ("S2025A", "2025年早稻", "2025-03-10", "2025-07-25", "HARVESTED"),
        ("S2025B", "2025年晚稻", "2025-07-20", "2025-11-05", "IN_PROGRESS"),
    ]
    for sid, (code, name, sowing, harvest, status) in enumerate(data, 1):
        seasons.append((sid, code, name, sowing, harvest, status))
    return seasons


def gen_farm_records(plots, seasons, farmers, admins):
    records = []
    attachments = []
    # 政府/农技员用户作为提交人
    submitter_ids = [uid for uid, role in admins if role in ("GOVERNMENT", "ADMIN")] or [1]

    season_dates = {
        1: (datetime(2024, 3, 15), datetime(2024, 7, 20)),
        2: (datetime(2024, 7, 25), datetime(2024, 11, 10)),
        3: (datetime(2025, 3, 10), datetime(2025, 7, 25)),
        4: (datetime(2025, 7, 20), datetime(2025, 11, 5)),
    }

    for plot in plots:
        plot_id = plot[0]
        area = plot[5]
        # 每块地参与 1-2 个种植季
        season_count = random.randint(1, 2)
        selected_seasons = random.sample(list(season_dates.keys()), season_count)

        for season_id in selected_seasons:
            start, end = season_dates[season_id]
            n = random.randint(SCALE["records_per_plot_season_min"], SCALE["records_per_plot_season_max"])

            # 该地块全年目标亩成本 600-700 元，均摊到本季
            # 若地块参与多季，则每季成本按比例减少，保证全年亩成本仍在 600-700
            season_target_cost = round(area * random.uniform(600, 700) / season_count, 2)
            cost_records = []
            harvest_records = []

            for _ in range(n):
                rid = next_id("farm_record")
                rtype = random.choices(RECORD_TYPES, weights=RECORD_TYPE_WEIGHTS)[0]
                rdate = rand_date(start, end)
                desc = f"{plot[4]} {rtype} 记录"
                material = None
                amount = None
                output = None

                submitted_by = random.choice(submitter_ids)
                status = random.choices(["SUBMITTED", "VERIFIED", "NEEDS_CORRECTION"], weights=[5, 4, 1])[0]

                if rtype in ("FERTILIZING", "PESTICIDE", "IRRIGATION"):
                    if rtype == "FERTILIZING":
                        material = random.choice(["有机肥", "复合肥", "尿素"])
                    elif rtype == "PESTICIDE":
                        material = random.choice(["生物农药", "低毒杀虫剂"])
                    else:
                        material = "灌溉用水"
                    cost_records.append((rid, plot_id, season_id, rtype, rdate, desc, material))
                elif rtype == "HARVEST":
                    # 亩产 800-1200 斤
                    output = round(area * random.uniform(800, 1200), 2)
                    records.append((rid, plot_id, season_id, rtype, rdate.strftime("%Y-%m-%d"), desc, material, amount, output, submitted_by, status))
                elif rtype == "QUALITY_TEST":
                    # 抽样检测产量
                    output = round(area * random.uniform(600, 1000), 2)
                    records.append((rid, plot_id, season_id, rtype, rdate.strftime("%Y-%m-%d"), desc, material, amount, output, submitted_by, status))
                else:
                    records.append((rid, plot_id, season_id, rtype, rdate.strftime("%Y-%m-%d"), desc, material, amount, output, submitted_by, status))

                if random.random() < SCALE["attachment_rate"]:
                    aid = next_id("record_attachment")
                    file_url = f"https://danqiu.example.com/record/{rid}/photo.jpg"
                    attachments.append((aid, rid, file_url, "IMAGE"))

            # 分摊成本到投入类记录
            if cost_records:
                weights = [random.uniform(0.5, 1.5) for _ in cost_records]
                total_w = sum(weights)
                for idx, (rid, plot_id, season_id, rtype, rdate, desc, material) in enumerate(cost_records):
                    amount = round(season_target_cost * weights[idx] / total_w, 2)
                    submitted_by = random.choice(submitter_ids)
                    status = random.choices(["SUBMITTED", "VERIFIED", "NEEDS_CORRECTION"], weights=[5, 4, 1])[0]
                    records.append((rid, plot_id, season_id, rtype, rdate.strftime("%Y-%m-%d"), desc, material, amount, None, submitted_by, status))

    return records, attachments


def gen_standards():
    versions = []
    clauses = []
    for i in range(1, SCALE["standard_versions"] + 1):
        vid = next_id("standard_version")
        version_no = f"V{i}.0"
        title = f"丹邱丝苗米全产业链标准 V{i}.0"
        status = ["RETIRED", "PUBLISHED", "DRAFT"][i - 1]
        published = rand_time_str(rand_date(datetime(2023, 1, 1), datetime(2025, 6, 1))) if status != "DRAFT" else None
        versions.append((vid, version_no, title, status, published))

        for j in range(SCALE["clauses_per_version"]):
            stage, code_tmpl, name_tmpl, req_tmpl = STANDARD_CLAUSE_TEMPLATES[j % len(STANDARD_CLAUSE_TEMPLATES)]
            cid = next_id("standard_clause")
            clause_code = code_tmpl.format(j + 1)
            clause_name = f"{name_tmpl} #{j+1}"
            requirement = req_tmpl
            check_rule = {
                "type": random.choice(["NUMERIC", "BOOLEAN", "SELECT"]),
                "threshold": random.choice(["≤0.05", "≥80", "合格"]),
                "unit": random.choice(["mg/kg", "分", "-"])
            }
            clauses.append((cid, vid, stage, clause_code, clause_name, requirement, check_rule))

    return versions, clauses


def gen_certifications(plots, versions, admins):
    certifications = []
    checks = []
    reviewer_ids = [uid for uid, role in admins if role in ("OPERATOR", "GOVERNMENT", "ADMIN")] or [1]

    # 每个认证对应一个 plot + farmer + standard
    sample_plots = random.sample(plots, min(SCALE["certifications"], len(plots)))
    for plot in sample_plots:
        plot_id = plot[0]
        farmer_id = plot[2]
        standard_id = random.randint(1, len(versions))
        cert_id = next_id("farmer_certification")
        status = random.choices(
            ["PENDING", "APPROVED", "REJECTED", "RECTIFYING"],
            weights=[2, 5, 2, 1]
        )[0]
        reviewer = random.choice(reviewer_ids) if status != "PENDING" else None
        note = random.choice([None, "符合标准要求", "需补充材料", "整改后复审"])
        submitted = rand_time_str(rand_date(datetime(2025, 1, 1), datetime(2026, 6, 1)))
        reviewed = rand_time_str(rand_date(datetime(2025, 2, 1), datetime(2026, 8, 1))) if status != "PENDING" else None
        certifications.append((cert_id, farmer_id, plot_id, standard_id, status, reviewer, note, submitted, reviewed))

        # 每个认证生成 10 条 clause check（使用该 standard 的 clauses）
        # 这里简化：所有版本都有 10 条 clauses，ID 连续
        start_clause = (standard_id - 1) * SCALE["clauses_per_version"] + 1
        for offset in range(SCALE["clauses_per_version"]):
            cid = next_id("certification_check")
            clause_id = start_clause + offset
            result = random.choices(["PASS", "FAIL", "PENDING"], weights=[7, 2, 1])[0]
            note_c = random.choice([None, "达标", "轻微不符"])
            checks.append((cid, cert_id, clause_id, result, note_c))

    return certifications, checks


def gen_inspections(plots, admins):
    inspections = []
    inspector_ids = [uid for uid, role in admins if role == "GOVERNMENT"] or [1]
    sample_plots = random.sample(plots, min(SCALE["inspections"], len(plots)))
    for plot in sample_plots:
        iid = next_id("field_inspection")
        inspector = random.choice(inspector_ids)
        date = rand_date(datetime(2025, 3, 1), datetime(2026, 8, 31))
        result = random.choices(["PASS", "WARNING", "FAIL"], weights=[6, 3, 1])[0]
        diff = random.choice([None, "记录与实际面积有偏差", "施肥记录缺失"]) if result != "PASS" else None
        rect = result == "FAIL" or (result == "WARNING" and random.random() < 0.3)
        inspections.append((iid, plot[0], inspector, date.strftime("%Y-%m-%d"), result, diff, rect))
    return inspections


def gen_reports(admins):
    reports = []
    confirmers = [uid for uid, role in admins if role in ("GOVERNMENT", "ADMIN")] or [1]
    periods = [
        ("WEEKLY", "2025-W10"), ("WEEKLY", "2025-W20"), ("WEEKLY", "2025-W30"),
        ("MONTHLY", "2025-05"), ("MONTHLY", "2025-06"), ("MONTHLY", "2025-07"),
        ("QUARTERLY", "2025-Q2"), ("QUARTERLY", "2025-Q3"),
        ("WEEKLY", "2026-W15"), ("MONTHLY", "2026-06"), ("MONTHLY", "2026-07"),
        ("QUARTERLY", "2026-Q2"),
    ]
    for rtype, period in periods[:SCALE["reports"]]:
        rid = next_id("regulatory_report")
        content = {
            "summary": f"{period} 丹邱村农业生产监管情况",
            "indicators": {"inspection_count": random.randint(5, 20), "pass_rate": round(random.uniform(0.8, 1.0), 2)},
            "abnormal_count": random.randint(0, 3)
        }
        status = random.choices(["DRAFT", "CONFIRMED", "ARCHIVED"], weights=[1, 6, 3])[0]
        confirmed_by = random.choice(confirmers) if status != "DRAFT" else None
        confirmed_at = rand_time_str(rand_date(datetime(2025, 3, 1), datetime(2026, 8, 31))) if status != "DRAFT" else None
        export_url = f"https://danqiu.example.com/reports/{rid}.pdf" if status != "DRAFT" else None
        reports.append((rid, rtype, period, content, status, confirmed_by, confirmed_at, export_url))
    return reports


def gen_insurance(plots, admins):
    policies = []
    claims = []
    entered_by = [uid for uid, role in admins if role in ("INSURANCE", "ADMIN")] or [1]
    reviewed_by = [uid for uid, role in admins if role == "ADMIN"] or [1]

    sample_plots = random.sample(plots, min(SCALE["policies"], len(plots)))
    for i, plot in enumerate(sample_plots, 1):
        pid = next_id("insurance_policy")
        policy_no = next_year_code("BO", 2025)
        farmer_id = plot[2]
        plot_id = plot[0]
        product_id = 1  # 已预置的保险产品
        area = plot[5]
        insured_amount = round(area * 1500, 2)
        total_premium = round(insured_amount * 0.05, 2)
        farmer_premium = round(total_premium * 0.2, 2)
        status = random.choices(["APPLIED", "ACTIVE", "EXPIRED", "CANCELLED"], weights=[2, 6, 1, 1])[0]
        applied_at = rand_time_str(rand_date(datetime(2024, 3, 1), datetime(2025, 12, 31)))
        policies.append((pid, policy_no, farmer_id, plot_id, product_id, area, insured_amount, total_premium, farmer_premium, status, applied_at))

    # 理赔只针对 ACTIVE/APPLIED 状态保单
    eligible_policies = [p for p in policies if p[9] in ("ACTIVE", "APPLIED")]
    claim_policies = random.sample(eligible_policies, min(SCALE["claims"], len(eligible_policies)))
    for policy in claim_policies:
        cid = next_id("insurance_claim")
        claim_no = next_year_code("CL", 2025)
        policy_id = policy[0]
        disaster_rate = round(random.uniform(0.1, 0.6), 4)
        claim_amount = round(policy[6] * disaster_rate, 2)
        enter = random.choice(entered_by)
        reviewer = random.choice(reviewed_by)
        status = random.choices(["SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"], weights=[1, 2, 3, 1, 3])[0]
        reviewed_at = rand_time_str(rand_date(datetime(2025, 4, 1), datetime(2026, 8, 31))) if status != "SUBMITTED" else None
        claims.append((cid, claim_no, policy_id, "受台风影响倒伏", disaster_rate, claim_amount, enter, reviewer, status, reviewed_at))

    return policies, claims


def gen_loans(plots):
    loans = []
    sample_plots = random.sample(plots, min(SCALE["loans"], len(plots)))
    for plot in sample_plots:
        lid = next_id("loan_application")
        app_no = next_year_code("LA", 2025)
        farmer_id = plot[2]
        plot_id = plot[0]
        area = plot[5]
        suggested = round(area * 800, 2)
        risk = random.choices(["LOW", "MEDIUM", "HIGH"], weights=[4, 5, 1])[0]
        result = random.choices(["PENDING", "APPROVED", "REJECTED"], weights=[3, 5, 2])[0]
        note = random.choice([None, "信用良好，建议授信", "需补充土地证明", "风险较高，审慎授信"])
        applied = rand_time_str(rand_date(datetime(2025, 1, 1), datetime(2026, 6, 1)))
        reviewed = rand_time_str(rand_date(datetime(2025, 2, 1), datetime(2026, 8, 1))) if result != "PENDING" else None
        loans.append((lid, app_no, farmer_id, plot_id, area, suggested, risk, result, note, applied, reviewed))
    return loans


def gen_trace_products(plots, seasons):
    trace_codes = []
    products = []
    for i in range(1, SCALE["trace_codes"] + 1):
        plot = random.choice(plots)
        season = random.choice(seasons)
        tid = next_id("trace_code")
        code = uuid.uuid4().hex[:16].upper()
        batch_name = f"{plot[4]} {season[2]} 批次"
        grade = random.choice(["SPECIAL", "FIRST", "SECOND"])
        report_url = f"https://danqiu.example.com/quality/{tid}.pdf"
        trace_codes.append((tid, code, plot[0], season[0], batch_name, grade, report_url, "ACTIVE"))

        pid = next_id("product")
        spec = random.choice(["5kg 装", "10kg 装", "礼盒装 2.5kg"])
        price_map = {"5kg 装": 68.0, "10kg 装": 128.0, "礼盒装 2.5kg": 88.0}
        price = price_map[spec]
        stock = random.randint(50, 500)
        status = "ON_SALE"
        products.append((pid, tid, f"丹邱丝苗米 {spec}", spec, price, stock, status))

    return trace_codes, products


def gen_adoptions(plots, consumers):
    adoptions = []
    for i in range(1, SCALE["adoptions"] + 1):
        plot = random.choice(plots)
        consumer = random.choice(consumers)
        aid = next_id("adoption_order")
        order_no = next_code("AD", datetime(2025, random.randint(1, 12), random.randint(1, 28)))
        fee = round(random.uniform(500, 3000), 2)
        status = random.choices(["PAID", "ACTIVE", "COMPLETED", "REFUNDED"], weights=[2, 4, 3, 1])[0]
        started = rand_time_str(rand_date(datetime(2025, 1, 1), datetime(2026, 6, 1)))
        adoptions.append((aid, order_no, consumer, plot[0], fee, status, started))
    return adoptions


def gen_orders(plots, consumers, products, trace_codes, plot_id_to_farmer):
    orders = []
    items = []
    shipments = []
    dividends = []

    product_list = list(products)
    product_id_to_plot = {}
    for p in products:
        # product -> trace_code -> plot_id
        trace_id = p[1]
        plot_id = next(t[2] for t in trace_codes if t[0] == trace_id)
        product_id_to_plot[p[0]] = plot_id

    for i in range(1, SCALE["orders"] + 1):
        order_date = rand_date(datetime(2025, 1, 1), datetime(2026, 8, 31))
        oid = next_id("sales_order")
        order_no = next_code("SO", order_date)
        consumer = random.choice(consumers)
        source = random.choices(["PLATFORM", "OTHER"], weights=[8, 2])[0]
        status = random.choices(
            ["PENDING_PAYMENT", "PAID", "SHIPPED", "COMPLETED", "CANCELLED", "REFUNDED"],
            weights=[1, 3, 4, 5, 1, 1]
        )[0]
        address = {
            "receiver": random.choice(CONSUMER_NAMES),
            "phone": f"138{random.randint(10000000, 99999999)}",
            "detail_address": f"广州市增城区{random.choice(['荔城街道', '增江街道', '朱村街道'])}某小区{random.randint(1, 20)}栋"
        }
        paid_at = rand_time_str(order_date + timedelta(hours=random.randint(1, 48))) if status in ("PAID", "SHIPPED", "COMPLETED") else None
        shipped_at = rand_time_str(order_date + timedelta(days=random.randint(1, 3))) if status in ("SHIPPED", "COMPLETED") else None
        completed_at = rand_time_str(order_date + timedelta(days=random.randint(3, 10))) if status == "COMPLETED" else None
        created_at = rand_time_str(order_date)
        orders.append((oid, order_no, consumer, 0.0, source, status, address, paid_at, shipped_at, completed_at, created_at))

        # 订单明细：1-3 个商品
        n_items = random.randint(1, 3)
        order_total = 0.0
        selected_products = random.sample(product_list, n_items)
        for prod in selected_products:
            iid = next_id("sales_order_item")
            qty = random.randint(1, 5)
            unit_price = prod[4]
            amount = round(qty * unit_price, 2)
            plot_id = product_id_to_plot[prod[0]]
            items.append((iid, oid, prod[0], plot_id, qty, unit_price, amount))
            order_total += amount

        # 更新订单总金额
        orders[-1] = (oid, order_no, consumer, round(order_total, 2), source, status, address, paid_at, shipped_at, completed_at, created_at)

        # 物流：已发货/已完成订单
        if status in ("SHIPPED", "COMPLETED"):
            sid = next_id("shipment")
            carrier = random.choice(CARRIERS)
            tracking = f"SF{random.randint(100000000000, 999999999999)}"
            shipments.append((sid, oid, carrier, tracking, shipped_at))

        # 分红：已完成订单
        if status == "COMPLETED":
            # 收集该订单涉及的地块和农户
            involved = {}
            for it in items[-n_items:]:
                plot_id = it[3]
                farmer_id = plot_id_to_farmer[plot_id]
                involved[(farmer_id, plot_id)] = involved.get((farmer_id, plot_id), 0.0) + float(it[6])
            for (farmer_id, plot_id), base in involved.items():
                did = next_id("farmer_dividend")
                rate = round(random.uniform(0.05, 0.15), 4)
                amount = round(base * rate, 2)
                div_status = random.choices(["CALCULATED", "PENDING_SETTLEMENT", "SETTLED"], weights=[2, 4, 4])[0]
                settled_at = completed_at if div_status == "SETTLED" else None
                dividends.append((did, oid, farmer_id, plot_id, round(base, 2), rate, amount, div_status, settled_at))

    return orders, items, shipments, dividends


def build_sql():
    users, user_roles, farmers, consumers, admins = gen_users()
    profiles = gen_farmer_profiles(farmers)
    plots, plot_id_to_farmer = gen_plots(farmers, profiles)
    seasons = gen_seasons()
    records, attachments = gen_farm_records(plots, seasons, farmers, admins)
    versions, clauses = gen_standards()
    certifications, checks = gen_certifications(plots, versions, admins)
    inspections = gen_inspections(plots, admins)
    reports = gen_reports(admins)
    policies, claims = gen_insurance(plots, admins)
    loans = gen_loans(plots)
    trace_codes, products = gen_trace_products(plots, seasons)
    adoptions = gen_adoptions(plots, consumers)
    orders, items, shipments, dividends = gen_orders(plots, consumers, products, trace_codes, plot_id_to_farmer)

    sql = []
    sql.append("USE `danqiu_rice`;\n")
    sql.append("SET FOREIGN_KEY_CHECKS = 0;\n")
    sql.append("SET NAMES utf8mb4;\n\n")

    # sys_role 已预置，跳过
    sql.append("-- 1. 用户与角色\n")
    sql.append(insert_sql("sys_user",
                          ["id", "username", "password_hash", "real_name", "phone", "status"],
                          [(u[0], sql_str(u[1]), sql_str(u[2]), sql_str(u[3]), sql_str(u[4]), sql_str(u[5])) for u in users]))
    sql.append(insert_sql("sys_user_role",
                          ["user_id", "role_id"],
                          [(ur[0], f"(SELECT id FROM sys_role WHERE role_code = {sql_str(ur[1])})") for ur in user_roles]))

    sql.append("-- 2. 农户与地块\n")
    sql.append(insert_sql("farmer_profile",
                          ["id", "user_id", "village", "address", "id_card_masked", "certification_status", "certification_at"],
                          [(p[0], p[1], sql_str(p[2]), sql_str(p[3]), sql_str(p[4]), sql_str(p[5]), sql_str(p[6])) for p in profiles]))
    sql.append(insert_sql("farm_plot",
                          ["id", "plot_code", "farmer_id", "plot_name", "village", "area_mu", "variety", "longitude", "latitude", "boundary_json", "satellite_image_url", "status"],
                          [(p[0], sql_str(p[1]), p[2], sql_str(p[3]), sql_str(p[4]), p[5], sql_str(p[6]), p[7] if p[7] is not None else "NULL", p[8] if p[8] is not None else "NULL", sql_json(p[9]), sql_str(p[10]), sql_str(p[11])) for p in plots]))

    sql.append("-- 3. 种植季与农事记录\n")
    sql.append(insert_sql("production_season",
                          ["id", "season_code", "season_name", "sowing_date", "harvest_date", "status"],
                          [(s[0], sql_str(s[1]), sql_str(s[2]), sql_str(s[3]), sql_str(s[4]), sql_str(s[5])) for s in seasons]))
    sql.append(insert_sql("farm_record",
                          ["id", "plot_id", "season_id", "record_type", "record_date", "description", "material_name", "material_amount", "output_jin", "submitted_by", "status"],
                          [(r[0], r[1], r[2], sql_str(r[3]), sql_str(r[4]), sql_str(r[5]), sql_str(r[6]), r[7] if r[7] is not None else "NULL", r[8] if r[8] is not None else "NULL", r[9], sql_str(r[10])) for r in records]))
    sql.append(insert_sql("record_attachment",
                          ["id", "record_id", "file_url", "file_type"],
                          [(a[0], a[1], sql_str(a[2]), sql_str(a[3])) for a in attachments]))

    sql.append("-- 4. 标准与认证\n")
    sql.append(insert_sql("standard_version",
                          ["id", "version_no", "title", "status", "published_at", "created_at"],
                          [(v[0], sql_str(v[1]), sql_str(v[2]), sql_str(v[3]), sql_str(v[4]), sql_str(rand_time_str(datetime(2023, 1, 1)))) for v in versions]))
    sql.append(insert_sql("standard_clause",
                          ["id", "standard_id", "stage", "clause_code", "clause_name", "requirement", "check_rule_json"],
                          [(c[0], c[1], sql_str(c[2]), sql_str(c[3]), sql_str(c[4]), sql_str(c[5]), sql_json(c[6])) for c in clauses]))
    sql.append(insert_sql("farmer_certification",
                          ["id", "farmer_id", "plot_id", "standard_id", "status", "reviewer_id", "review_note", "submitted_at", "reviewed_at"],
                          [(c[0], c[1], c[2], c[3], sql_str(c[4]), c[5] if c[5] else "NULL", sql_str(c[6]), sql_str(c[7]), sql_str(c[8])) for c in certifications]))
    sql.append(insert_sql("certification_check",
                          ["id", "certification_id", "clause_id", "result", "note"],
                          [(c[0], c[1], c[2], sql_str(c[3]), sql_str(c[4])) for c in checks]))

    sql.append("-- 5. 监管\n")
    sql.append(insert_sql("field_inspection",
                          ["id", "plot_id", "inspector_id", "inspection_date", "result", "difference_note", "rectification_required", "created_at"],
                          [(i[0], i[1], i[2], sql_str(i[3]), sql_str(i[4]), sql_str(i[5]), sql_bool(i[6]), sql_str(rand_time_str(datetime(2025, 3, 1)))) for i in inspections]))
    sql.append(insert_sql("regulatory_report",
                          ["id", "report_type", "report_period", "content_json", "status", "confirmed_by", "confirmed_at", "export_file_url", "created_at"],
                          [(r[0], sql_str(r[1]), sql_str(r[2]), sql_json(r[3]), sql_str(r[4]), r[5] if r[5] else "NULL", sql_str(r[6]), sql_str(r[7]), sql_str(rand_time_str(datetime(2025, 3, 1)))) for r in reports]))

    sql.append("-- 6. 保险与贷款\n")
    sql.append(insert_sql("insurance_policy",
                          ["id", "policy_no", "farmer_id", "plot_id", "product_id", "insured_area_mu", "insured_amount", "total_premium", "farmer_premium", "status", "applied_at"],
                          [(p[0], sql_str(p[1]), p[2], p[3], p[4], p[5], p[6], p[7], p[8], sql_str(p[9]), sql_str(p[10])) for p in policies]))
    sql.append(insert_sql("insurance_claim",
                          ["id", "claim_no", "policy_id", "disaster_note", "disaster_rate", "claim_amount", "entered_by", "reviewed_by", "status", "reviewed_at"],
                          [(c[0], sql_str(c[1]), c[2], sql_str(c[3]), c[4], c[5], c[6], c[7], sql_str(c[8]), sql_str(c[9])) for c in claims]))
    sql.append(insert_sql("loan_application",
                          ["id", "application_no", "farmer_id", "plot_id", "area_mu", "suggested_amount", "risk_level", "bank_result", "bank_note", "applied_at", "reviewed_at"],
                          [(l[0], sql_str(l[1]), l[2], l[3], l[4], l[5], sql_str(l[6]), sql_str(l[7]), sql_str(l[8]), sql_str(l[9]), sql_str(l[10])) for l in loans]))

    sql.append("-- 7. 溯源、认养、商城与分红\n")
    sql.append(insert_sql("trace_code",
                          ["id", "code", "plot_id", "season_id", "batch_name", "product_grade", "quality_report_url", "status", "created_at"],
                          [(t[0], sql_str(t[1]), t[2], t[3], sql_str(t[4]), sql_str(t[5]), sql_str(t[6]), sql_str(t[7]), sql_str(rand_time_str(datetime(2025, 1, 1)))) for t in trace_codes]))
    sql.append(insert_sql("product",
                          ["id", "trace_code_id", "product_name", "specification", "price", "stock", "status"],
                          [(p[0], p[1], sql_str(p[2]), sql_str(p[3]), p[4], p[5], sql_str(p[6])) for p in products]))
    sql.append(insert_sql("adoption_order",
                          ["id", "order_no", "consumer_user_id", "plot_id", "fee", "status", "started_at"],
                          [(a[0], sql_str(a[1]), a[2], a[3], a[4], sql_str(a[5]), sql_str(a[6])) for a in adoptions]))
    sql.append(insert_sql("sales_order",
                          ["id", "order_no", "consumer_user_id", "total_amount", "source", "status", "address_snapshot", "paid_at", "shipped_at", "completed_at", "created_at"],
                          [(o[0], sql_str(o[1]), o[2], o[3], sql_str(o[4]), sql_str(o[5]), sql_json(o[6]), sql_str(o[7]), sql_str(o[8]), sql_str(o[9]), sql_str(o[10])) for o in orders]))
    sql.append(insert_sql("sales_order_item",
                          ["id", "order_id", "product_id", "plot_id", "quantity", "unit_price", "amount"],
                          [(it[0], it[1], it[2], it[3], it[4], it[5], it[6]) for it in items]))
    sql.append(insert_sql("shipment",
                          ["id", "order_id", "carrier", "tracking_no", "shipped_at"],
                          [(s[0], s[1], sql_str(s[2]), sql_str(s[3]), sql_str(s[4])) for s in shipments]))
    sql.append(insert_sql("farmer_dividend",
                          ["id", "order_id", "farmer_id", "plot_id", "base_amount", "dividend_rate", "dividend_amount", "status", "settled_at"],
                          [(d[0], d[1], d[2], d[3], d[4], d[5], d[6], sql_str(d[7]), sql_str(d[8])) for d in dividends]))

    sql.append("SET FOREIGN_KEY_CHECKS = 1;\n")

    return "\n".join(sql)


def main():
    sql_content = build_sql()
    OUTPUT_SQL.write_text(sql_content, encoding="utf-8")
    print(f"Generated {OUTPUT_SQL}")
    print(f"Total size: {len(sql_content)} bytes")


if __name__ == "__main__":
    main()
