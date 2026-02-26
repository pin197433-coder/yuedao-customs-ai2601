import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io
import re
import urllib.parse

# 页面配置
st.set_page_config(
    page_title="粤道海关数据AI助手 - 免费版", 
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 粤道产品知识库 ====================
YUEDAO_PROFILE = {
    "company_name": "CloudTop Cable / Yuedao",
    "products": [
        "Cat6/Cat6A结构化布线（LSZH阻燃）",
        "光纤布线系统（MPO/MTP预端接）", 
        "安防线缆（CCTV同轴/控制线/报警线）",
        "数据中心模块化布线"
    ],
    "advantages": [
        "广州地铁/深圳机场等政府项目背书",
        "LSZH低烟无卤认证（中东/欧洲刚需）",
        "模块化数据中心预端接方案",
        "价格比CommScope/Panduit低30%"
    ],
    "target_title": ["Procurement Manager", "Purchasing Manager", "Sourcing Manager", 
                    "Buyer", "GM", "Managing Director", "Owner", "Project Manager"]
}

# ==================== 邮箱生成引擎 ====================
EMAIL_PATTERNS = {
    "default": ["info@", "sales@", "contact@", "support@"],
    "procurement": ["procurement@", "purchasing@", "buyer@", "sourcing@", "supply@"],
    "management": ["gm@", "md@", "director@", "ceo@", "manager@"]
}

COUNTRY_EMAIL_PATTERNS = {
    "UAE": ["sales@", "info@", "procurement@", "purchasing@"],
    "Saudi": ["info@", "sales@", "purchasing@", "procurement@"],
    "USA": ["sales@", "info@", "contact@", "buyers@"],
    "UK": ["info@", "sales@", "enquiries@", "buying@"],
    "Germany": ["info@", "vertrieb@", "einkauf@", "geschaeftsfuehrung@"],
    "France": ["contact@", "ventes@", "achats@", "direction@"],
    "Australia": ["info@", "sales@", "purchasing@", "buyer@"],
    "India": ["info@", "sales@", "purchase@", "procurement@"],
    "South Africa": ["info@", "sales@", "purchasing@", "procurement@"]
}

def generate_email_variations(company_name, country="General", person_name=None):
    """生成邮箱变体"""
    # 清理公司名
    clean_name = re.sub(r'[^\w\s]', '', company_name).strip().lower()
    clean_name = clean_name.replace(" ", "").replace(",", "").replace(".", "")
    
    # 常见域名后缀
    domains = [
        f"{clean_name}.com",
        f"{clean_name}.net", 
        f"{clean_name}.co.{country.lower() if country != 'General' else 'com'}",
        f"{clean_name}.com.{country.lower() if country in ['au', 'uk'] else ''}",
        f"{clean_name}group.com",
        f"{clean_name}trading.com",
        f"{clean_name}cable.com",
        f"{clean_name}elec.com"
    ]
    
    # 去重和清理
    domains = list(set([d for d in domains if d.endswith(('.com', '.net', '.co.', '.com.au', '.co.uk', '.de', '.fr', '.ae', '.sa'))]))
    
    emails = []
    patterns = COUNTRY_EMAIL_PATTERNS.get(country, EMAIL_PATTERNS["default"] + EMAIL_PATTERNS["procurement"])
    
    for domain in domains[:3]:  # 限制前3个域名
        for pattern in patterns[:4]:  # 限制前4个前缀
            emails.append(f"{pattern}{domain}")
            
    # 如果提供了人名，生成个人邮箱
    if person_name and len(person_name) > 2:
        names = person_name.lower().split()
        if len(names) >= 2:
            first, last = names[0], names[-1]
            f_initial = first[0]
            variations = [
                f"{first}.{last}@{domains[0]}",
                f"{f_initial}{last}@{domains[0]}",
                f"{first}{last}@{domains[0]}",
                f"{last}.{first}@{domains[0]}"
            ]
            emails = variations + emails
            
    return list(set(emails))[:8]  # 返回最多8个

def generate_linkedin_search(company_name, country=""):
    """生成LinkedIn搜索指令"""
    base_query = f'site:linkedin.com/in ("procurement manager" OR "purchasing manager" OR "buyer" OR "sourcing" OR "general manager") AND "{company_name}"'
    if country:
        base_query += f' AND "{country}"'
    return base_query

def generate_rocketreach_url(company_name):
    """生成RocketReach搜索链接"""
    encoded = urllib.parse.quote(company_name)
    return f"https://rocketreach.co/{encoded}-profile"

def generate_hunter_url(domain):
    """生成Hunter.io链接"""
    return f"https://hunter.io/search/{domain}"

def get_mailtester_link(email):
    """生成MailTester验证链接"""
    return f"https://mailtester.com/test-smtp.php?email={urllib.parse.quote(email)}"

# ==================== AI分析引擎（规则版，无需API） ====================
def analyze_importer(row):
    """分析进口商匹配度"""
    company = str(row.get('company_name', ''))
    products = str(row.get('products', '')).upper()
    country = str(row.get('country', 'Unknown'))
    value = float(row.get('total_value', 0)) if pd.notna(row.get('total_value')) else 0
    shipments = int(row.get('shipment_count', 1)) if pd.notna(row.get('shipment_count')) else 1
    
    score = 0
    reasons = []
    recommended_products = []
    
    # 产品匹配度计算
    if any(k in products for k in ['CAT6', 'CAT5', 'ETHERNET', 'LAN', 'NETWORK CABLE']):
        score += 35
        reasons.append("结构化布线需求明确")
        recommended_products.append("Cat6A LSZH综合布线")
        
    if any(k in products for k in ['FIBER', 'OPTICAL', 'MPO', 'MTP']):
        score += 40
        reasons.append("光纤基础设施需求")
        recommended_products.append("数据中心光纤系统")
        
    if any(k in products for k in ['CCTV', 'SECURITY', 'COAXIAL', 'RG59', 'RG6', 'ALARM']):
        score += 30
        reasons.append("安防线缆需求")
        recommended_products.append("CCTV专用线缆")
        
    if any(k in products for k in ['DATA CENTER', 'SERVER', 'RACK', 'INFRASTRUCTURE']):
        score += 45
        reasons.append("数据中心基建")
        recommended_products.append("模块化数据中心布线")
    
    # 进口频次（经销商特征）
    if shipments >= 6:
        score += 15
        reasons.append("高频进口（专业经销商）")
    elif shipments >= 3:
        score += 10
        reasons.append("规律进口")
    
    # 货值判断
    if 30000 <= value <= 500000:
        score += 15
        reasons.append("经销商级别采购额")
    elif value > 500000:
        score += 10
        reasons.append("大型进口商")
    
    # 国家加分（重点市场）
    high_potential_countries = ['UAE', 'Saudi Arabia', 'USA', 'Australia', 'South Africa', 'UK', 'Germany']
    if any(c in country for c in high_potential_countries):
        score += 5
        reasons.append(f"{country}为重点开拓市场")
    
    # 确定级别
    if score >= 80:
        tier = "A"
        priority = "🔴 立即跟进"
    elif score >= 60:
        tier = "B"
        priority = "🟡 重点培养"
    else:
        tier = "C"
        priority = "🟢 观察/群发"
    
    # 生成联系策略
    emails = generate_email_variations(company, country)
    linkedin_search = generate_linkedin_search(company, country)
    rocket_url = generate_rocketreach_url(company)
    
    return {
        "match_score": min(score, 100),
        "tier": tier,
        "priority": priority,
        "reasons": "；".join(reasons),
        "recommended_products": " + ".join(recommended_products) if recommended_products else "标准产品线",
        "suggested_emails": "; ".join(emails[:3]),
        "all_emails": emails,
        "linkedin_search": linkedin_search,
        "rocketreach_url": rocket_url,
        "verification_strategy": f"1) 先验证 {emails[0]} 2) 无效则试 {emails[1]} 3) LinkedIn搜索决策人",
        "country": country
    }

# ==================== 邮件模板生成器 ====================
def generate_email_template(company_name, tier, products, country):
    """生成个性化开发信模板"""
    
    if tier == "A":
        subject = f"Strategic Partnership: LSZH Cables for {company_name} - 30% Cost Advantage"
        body = f"""Dear Procurement Manager,

Noticed {company_name}'s regular imports of {products} from China. 

We are CloudTop Cable (Yuedao), supplying Cat6A LSZH and Fiber solutions to Guangzhou Metro and airports.

Why consider us:
✓ Same quality as CommScope, 30% lower cost
✓ LSZH certification (critical for {country} fire safety standards)
✓ Modular data center pre-terminated solutions (reduce installation time 50%)

Can we schedule a 15-min call next week to discuss your Q3 cabling needs?

Best,
[Your Name]
CloudTop Cable | www.cloudtopcable.com
WhatsApp: [Your Number]

P.S. Sample kit available for qualified distributors."""
    
    elif tier == "B":
        subject = f"China Direct Supply: {products} for {company_name}"
        body = f"""Hi Team,

Came across your company while researching {country} cabling distributors.

We manufacture Cat6/Cat6A and fiber optic cables with:
• CE/UL/CPR certifications
• Project references: Metro systems, Data Centers
• MOQ as low as 500m for trial orders

Would you be interested in our 2025 price list?

Regards,
[Your Name]
CloudTop Cable"""
    
    else:
        subject = f"Cable Supplier Introduction - CloudTop/Yuedao"
        body = f"""Hello,

We are a structured cabling manufacturer from China, supplying Cat6/Fiber/Security cables.

Attached catalog for your reference. Any interest in adding our products to your lineup?

Best regards,
[Your Name]"""
    
    return {"subject": subject, "body": body}

# ==================== Streamlit UI ====================
st.title("🎯 粤道海关数据AI助手 - 免费决策人挖掘版")
st.markdown("""
**核心功能：** 海关数据AI分级 | 自动生成邮箱 | LinkedIn搜索指令 | 开发信模板  
**替代方案：** 无需Sales Navigator，使用RocketReach免费版+邮箱猜测公式
""")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 配置面板")
    
    st.markdown("**📧 邮箱验证工具：**")
    st.markdown("- [RocketReach](https://rocketreach.co) (25次免费/月)")
    st.markdown("- [Hunter.io](https://hunter.io) (25次免费/月)")
    st.markdown("- [MailTester](https://mailtester.com) (无限免费)")
    
    st.markdown("**🔗 LinkedIn搜索：**")
    st.markdown("使用下方生成的搜索指令在Google搜索")
    
    st.markdown("---")
    st.markdown("**💡 使用流程：**")
    st.markdown("1. 上传ImportYeti CSV")
    st.markdown("2. AI自动分级(A/B/C)")
    st.markdown("3. 复制LinkedIn指令找决策人")
    st.markdown("4. 用RocketReach查邮箱")
    st.markdown("5. 发送个性化开发信")

# 主界面
uploaded_file = st.file_uploader("📤 上传海关数据CSV (ImportYeti/TradeMap格式)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success(f"✅ 成功加载 {len(df)} 条进口记录")
    
    with st.expander("👀 预览原始数据"):
        st.dataframe(df.head(3))
    
    if st.button("🚀 开始AI分析 + 生成联系策略", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        for idx, row in df.iterrows():
            status_text.text(f"正在分析 {idx+1}/{len(df)}: {row.get('company_name', 'Unknown')}...")
            
            analysis = analyze_importer(row)
            email_template = generate_email_template(
                row.get('company_name', ''),
                analysis['tier'],
                analysis['recommended_products'],
                analysis['country']
            )
            
            results.append({
                "公司名": row.get('company_name'),
                "国家": analysis['country'],
                "匹配度": analysis['match_score'],
                "级别": analysis['tier'],
                "优先级": analysis['priority'],
                "推荐理由": analysis['reasons'],
                "推荐产品": analysis['recommended_products'],
                "猜测邮箱": analysis['suggested_emails'],
                "LinkedIn搜索指令": analysis['linkedin_search'],
                "RocketReach链接": analysis['rocketreach_url'],
                "验证策略": analysis['verification_strategy'],
                "邮件主题": email_template['subject'],
                "邮件正文": email_template['body']
            })
            
            progress_bar.progress((idx + 1) / len(df))
        
        status_text.empty()
        progress_bar.empty()
        
        results_df = pd.DataFrame(results)
        
        # 统计面板
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            a_count = len(results_df[results_df['级别']=='A'])
            st.metric("🔴 A级客户", a_count, f"立即跟进")
        with col2:
            b_count = len(results_df[results_df['级别']=='B'])
            st.metric("🟡 B级客户", b_count, f"重点培养")
        with col3:
            c_count = len(results_df[results_df['级别']=='C'])
            st.metric("🟢 C级客户", c_count, f"群发/观察")
        with col4:
            avg_score = results_df['匹配度'].mean()
            st.metric("平均匹配度", f"{avg_score:.1f}分")
        
        # 详细展示
        st.markdown("---")
        st.subheader("📊 客户分级清单")
        
        # A级客户（重点展示）
        with st.expander("🔴 A级客户 - 立即跟进（高匹配度经销商）", expanded=True):
            a_df = results_df[results_df['级别']=='A'].sort_values('匹配度', ascending=False)
            if not a_df.empty:
                for idx, row in a_df.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.markdown(f"**{row['公司名']}** ({row['国家']})")
                            st.caption(f"匹配度: {row['匹配度']}分 | {row['推荐理由']}")
                            st.markdown(f"🎯 **推荐产品:** {row['推荐产品']}")
                        with col2:
                            st.markdown("**📧 联系策略:**")
                            st.code(row['猜测邮箱'], language=None)
                            first_email = row['猜测邮箱'].split(';')[0].strip()
                            st.markdown(f"[验证邮箱]({get_mailtester_link(first_email)})")
                        with col3:
                            st.markdown("**🔗 工具链接:**")
                            st.markdown(f"[RocketReach]({row['RocketReach链接']})")
                            st.button(f"复制搜索指令_{idx}", key=f"copy_{idx}", 
                                    on_click=lambda x=row['LinkedIn搜索指令']: st.write(x))
                        st.markdown("---")
            else:
                st.info("未发现A级客户，建议放宽筛选条件")
        
        # B级客户
        with st.expander("🟡 B级客户 - 潜力培养"):
            b_df = results_df[results_df['级别']=='B']
            if not b_df.empty:
                st.dataframe(b_df[['公司名', '国家', '匹配度', '推荐产品', '猜测邮箱']], 
                           use_container_width=True, hide_index=True)
        
        # C级客户
        with st.expander("🟢 C级客户 - 观察/批量开发"):
            c_df = results_df[results_df['级别']=='C']
            if not c_df.empty:
                st.dataframe(c_df[['公司名', '国家', '匹配度', '猜测邮箱']], 
                           use_container_width=True, hide_index=True)
        
        # Excel导出（包含邮件模板）
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 分Sheet导出
            for tier, color in [('A', '红色'), ('B', '黄色'), ('C', '绿色')]:
                tier_df = results_df[results_df['级别']==tier]
                if not tier_df.empty:
                    tier_df.to_excel(writer, sheet_name=f'{tier}级客户', index=False)
            
            # 全部数据
            results_df.to_excel(writer, sheet_name='全部客户联系表', index=False)
            
            # 单独Sheet放邮件模板（方便复制）
            templates_df = results_df[['公司名', '邮件主题', '邮件正文']].copy()
            templates_df.to_excel(writer, sheet_name='邮件模板', index=False)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 下载完整Excel（含联系策略+邮件模板）",
                data=output.getvalue(),
                file_name=f"粤道海关客户开发表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col2:
            # CSV格式（适合导入CRM）
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 下载CSV（导入HubSpot/Zoho）",
                data=csv,
                file_name=f"海关客户_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.success("✅ 分析完成！建议：A级客户逐个验证邮箱+LinkedIn精准开发，B/C级批量邮件")

else:
    # 空状态示例
    st.info("👆 请上传海关数据CSV开始分析")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **📋 CSV文件应包含列：**
        - `company_name` / `importer_name`（公司名称）
        - `country`（国家）
        - `products` / `product_desc`（进口产品描述）
        - `total_value`（总货值，可选）
        - `shipment_count`（进口频次，可选）
        """)
    with col2:
        st.markdown("""
        **🎯 分析维度：**
        - 产品匹配度（Cat6/Fiber/Security）
        - 进口频次（判断是否为经销商）
        - 货值规模（判断客户层级）
        - 国家市场（重点市场加权）
        
        **📧 自动输出：**
        - 猜测邮箱（5-8个格式）
        - LinkedIn搜索指令
        - RocketReach直达链接
        - 个性化开发信模板
        """)

# 页脚
st.markdown("---")
st.caption("💡 提示：若邮箱验证失败，使用LinkedIn搜索指令在Google查找决策人，再通过RocketReach免费版查邮箱")
