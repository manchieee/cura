#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cura PDF Generator
4つのPDFを生成するスクリプト
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ============================================================
# フォント登録
# ============================================================
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

FONT_NORMAL = 'HeiseiKakuGo-W5'
FONT_BOLD = 'HeiseiKakuGo-W5'

# ============================================================
# カラー定義
# ============================================================
ROSE = colors.HexColor('#8a3a55')
ROSE_LIGHT = colors.HexColor('#f9f0f3')
GOLD = colors.HexColor('#c9a882')
NAVY = colors.HexColor('#2a1f1a')
LIGHT_GRAY = colors.HexColor('#f5f5f5')
WHITE = colors.white
BLACK = colors.black
GREEN = colors.HexColor('#2e7d32')
RED = colors.HexColor('#c62828')

OUTPUT_DIR = '/Users/munchie/Library/Mobile Documents/com~apple~CloudDocs/cura'

# ============================================================
# スタイル定義
# ============================================================
def get_styles():
    styles = {}

    styles['title'] = ParagraphStyle(
        'title',
        fontName=FONT_BOLD,
        fontSize=20,
        textColor=ROSE,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    styles['subtitle'] = ParagraphStyle(
        'subtitle',
        fontName=FONT_NORMAL,
        fontSize=11,
        textColor=GOLD,
        spaceAfter=12,
        alignment=TA_LEFT,
    )
    styles['section'] = ParagraphStyle(
        'section',
        fontName=FONT_BOLD,
        fontSize=13,
        textColor=ROSE,
        spaceBefore=14,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    styles['subsection'] = ParagraphStyle(
        'subsection',
        fontName=FONT_BOLD,
        fontSize=11,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    styles['body'] = ParagraphStyle(
        'body',
        fontName=FONT_NORMAL,
        fontSize=9,
        textColor=NAVY,
        spaceAfter=4,
        leading=14,
        alignment=TA_LEFT,
    )
    styles['body_small'] = ParagraphStyle(
        'body_small',
        fontName=FONT_NORMAL,
        fontSize=8,
        textColor=NAVY,
        spaceAfter=3,
        leading=12,
        alignment=TA_LEFT,
    )
    styles['note'] = ParagraphStyle(
        'note',
        fontName=FONT_NORMAL,
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        spaceAfter=4,
        leading=12,
        alignment=TA_LEFT,
    )
    styles['bullet'] = ParagraphStyle(
        'bullet',
        fontName=FONT_NORMAL,
        fontSize=9,
        textColor=NAVY,
        spaceAfter=3,
        leading=14,
        leftIndent=12,
        alignment=TA_LEFT,
    )
    styles['numbered'] = ParagraphStyle(
        'numbered',
        fontName=FONT_NORMAL,
        fontSize=9,
        textColor=NAVY,
        spaceAfter=6,
        leading=14,
        leftIndent=16,
        firstLineIndent=-16,
        alignment=TA_LEFT,
    )
    styles['bold_body'] = ParagraphStyle(
        'bold_body',
        fontName=FONT_BOLD,
        fontSize=9,
        textColor=NAVY,
        spaceAfter=4,
        leading=14,
        alignment=TA_LEFT,
    )
    styles['date'] = ParagraphStyle(
        'date',
        fontName=FONT_NORMAL,
        fontSize=8,
        textColor=colors.HexColor('#888888'),
        spaceAfter=4,
        alignment=TA_RIGHT,
    )
    return styles

# ============================================================
# ヘルパー: ヘッダーブロック生成
# ============================================================
def make_header(title, subtitle, styles):
    elems = []
    # 上部ライン
    elems.append(HRFlowable(width='100%', thickness=3, color=ROSE, spaceAfter=8))
    elems.append(Paragraph(title, styles['title']))
    if subtitle:
        elems.append(Paragraph(subtitle, styles['subtitle']))
    elems.append(HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=12))
    return elems

# ============================================================
# ヘルパー: テーブル標準スタイル
# ============================================================
def standard_table_style(header_bg=ROSE, alt_bg=LIGHT_GRAY, font_name=FONT_NORMAL):
    return TableStyle([
        # ヘッダー
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        # データ行
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        # 罫線
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, GOLD),
    ])

def add_alternating_rows(style, num_rows, alt_bg=LIGHT_GRAY):
    """偶数行（0-indexed: 2, 4, 6...）に薄いグレーを設定"""
    for i in range(2, num_rows, 2):
        style.add('BACKGROUND', (0, i), (-1, i), alt_bg)

# ============================================================
# PDF 1: cura 収支計画 現実版.pdf
# ============================================================
def generate_pdf1():
    path = os.path.join(OUTPUT_DIR, 'cura 収支計画 現実版.pdf')
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title='cura 収支計画（現実版）',
        author='cura',
    )
    styles = get_styles()
    elems = []

    # ヘッダー
    elems += make_header(
        'cura 収支計画（現実版）',
        'フェーズ1：まさみ＋看護師（業務委託）2名体制',
        styles
    )

    # ============ 開業タイムライン ============
    elems.append(Paragraph('開業までのタイムライン', styles['section']))

    timeline_data = [
        ['時期', '内容'],
        ['〜7月', '夏ボーナス受取・退職意思表示 ／ 有給34日消化スタート'],
        ['7〜9月', '給付中・準備期間 ／ HP公開・ケアマネ挨拶回り・問い合わせを温める\n契約・金銭授受はゼロ'],
        ['9月', '開業日・開業届提出 ／ 温めてた問い合わせに一斉連絡→初月複数件狙い'],
    ]
    t = Table(timeline_data, colWidths=[45*mm, 115*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(timeline_data))
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 10))

    # ============ フェーズ1 ============
    elems.append(Paragraph('フェーズ1　開業1〜2ヶ月目（週1件・月4件ペース）', styles['section']))

    # 収入
    elems.append(Paragraph('■ 収入', styles['subsection']))
    income1 = [
        ['項目', '金額', '内訳'],
        ['入会金', '¥60,000', '月1件 × ¥60,000'],
        ['プライベートケア', '¥144,000', '月4件 × 3h × ¥12,000'],
        ['夜間オンコール', '¥17,000', '1契約'],
        ['売上合計', '¥221,000', ''],
    ]
    t = Table(income1, colWidths=[60*mm, 40*mm, 60*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(income1))
    # 合計行をゴールド背景に
    ts.add('BACKGROUND', (0, len(income1)-1), (-1, len(income1)-1), GOLD)
    ts.add('TEXTCOLOR', (0, len(income1)-1), (-1, len(income1)-1), WHITE)
    ts.add('FONTNAME', (0, len(income1)-1), (-1, len(income1)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 6))

    # 支出
    elems.append(Paragraph('■ 支出', styles['subsection']))
    expense1 = [
        ['項目', '金額', '内訳'],
        ['看護師報酬（固定）', '¥50,000', '待機・顧問料'],
        ['通信・システム', '¥15,000', '携帯・クラウド等'],
        ['交通費', '¥5,000', '自転車中心'],
        ['支出合計', '¥70,000', ''],
    ]
    t = Table(expense1, colWidths=[60*mm, 40*mm, 60*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(expense1))
    ts.add('BACKGROUND', (0, len(expense1)-1), (-1, len(expense1)-1), ROSE)
    ts.add('TEXTCOLOR', (0, len(expense1)-1), (-1, len(expense1)-1), WHITE)
    ts.add('FONTNAME', (0, len(expense1)-1), (-1, len(expense1)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 6))

    elems.append(Paragraph('手残り（まさみ報酬前）：＋¥151,000', styles['bold_body']))
    elems.append(Paragraph('注記：まさみの生活費は失業給付でカバーする期間。赤字にならないのは強い。', styles['note']))
    elems.append(Spacer(1, 10))

    # ============ フェーズ2 ============
    elems.append(Paragraph('フェーズ2　開業3〜4ヶ月目（週2件・月8件ペース）', styles['section']))

    elems.append(Paragraph('■ 収入', styles['subsection']))
    income2 = [
        ['項目', '金額', '内訳'],
        ['入会金', '¥120,000', '月2件 × ¥60,000'],
        ['プライベートケア', '¥288,000', '月8件 × 3h × ¥12,000'],
        ['看護師同行プラン', '¥54,000', '月1件 × 3h × ¥18,000'],
        ['夜間オンコール', '¥51,000', '3契約 × ¥17,000'],
        ['売上合計', '¥513,000', ''],
    ]
    t = Table(income2, colWidths=[60*mm, 40*mm, 60*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(income2))
    ts.add('BACKGROUND', (0, len(income2)-1), (-1, len(income2)-1), GOLD)
    ts.add('TEXTCOLOR', (0, len(income2)-1), (-1, len(income2)-1), WHITE)
    ts.add('FONTNAME', (0, len(income2)-1), (-1, len(income2)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 6))

    elems.append(Paragraph('■ 支出', styles['subsection']))
    expense2 = [
        ['項目', '金額', '内訳'],
        ['看護師報酬（固定＋稼働）', '¥65,000', '固定5万＋同行1件分'],
        ['通信・システム', '¥15,000', ''],
        ['交通費', '¥10,000', ''],
        ['まさみ報酬', '¥150,000', '最低限の生活費'],
        ['支出合計', '¥240,000', ''],
    ]
    t = Table(expense2, colWidths=[60*mm, 40*mm, 60*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(expense2))
    ts.add('BACKGROUND', (0, len(expense2)-1), (-1, len(expense2)-1), ROSE)
    ts.add('TEXTCOLOR', (0, len(expense2)-1), (-1, len(expense2)-1), WHITE)
    ts.add('FONTNAME', (0, len(expense2)-1), (-1, len(expense2)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 6))

    elems.append(Paragraph('手残り：＋¥273,000', styles['bold_body']))
    elems.append(Paragraph('注記：ここからまさみ報酬を取り始める。黒字で安定軌道。', styles['note']))
    elems.append(Spacer(1, 10))

    # ============ フェーズ3 ============
    elems.append(Paragraph('フェーズ3　開業5〜6ヶ月目（週3件・月12件 ／ スタッフ検討期）', styles['section']))

    elems.append(Paragraph('■ 収入', styles['subsection']))
    income3 = [
        ['項目', '金額', '内訳'],
        ['入会金', '¥120,000', '月2件 × ¥60,000'],
        ['プライベートケア', '¥432,000', '月12件 × 3h × ¥12,000'],
        ['看護師同行プラン', '¥108,000', '月2件 × 3h × ¥18,000'],
        ['夜間オンコール', '¥85,000', '5契約 × ¥17,000'],
        ['売上合計', '¥745,000', ''],
    ]
    t = Table(income3, colWidths=[60*mm, 40*mm, 60*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(income3))
    ts.add('BACKGROUND', (0, len(income3)-1), (-1, len(income3)-1), GOLD)
    ts.add('TEXTCOLOR', (0, len(income3)-1), (-1, len(income3)-1), WHITE)
    ts.add('FONTNAME', (0, len(income3)-1), (-1, len(income3)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 6))

    elems.append(Paragraph('■ 支出', styles['subsection']))
    expense3 = [
        ['項目', '金額', '内訳'],
        ['看護師報酬', '¥80,000', '固定＋稼働増'],
        ['通信・システム', '¥15,000', ''],
        ['交通費', '¥15,000', ''],
        ['まさみ報酬', '¥200,000', ''],
        ['支出合計', '¥310,000', ''],
    ]
    t = Table(expense3, colWidths=[60*mm, 40*mm, 60*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(expense3))
    ts.add('BACKGROUND', (0, len(expense3)-1), (-1, len(expense3)-1), ROSE)
    ts.add('TEXTCOLOR', (0, len(expense3)-1), (-1, len(expense3)-1), WHITE)
    ts.add('FONTNAME', (0, len(expense3)-1), (-1, len(expense3)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 6))

    elems.append(Paragraph('手残り：＋¥435,000', styles['bold_body']))
    elems.append(Paragraph('注記：ここでタスケ等への声かけを検討。月12件はまさみ1人の限界ライン。', styles['note']))

    # フッター
    elems.append(Spacer(1, 16))
    elems.append(HRFlowable(width='100%', thickness=1, color=GOLD))
    elems.append(Paragraph('cura ／ 文京区千石4-43 ／ 更新：2026年4月', styles['note']))

    doc.build(elems)
    print(f'生成完了: {path}')

# ============================================================
# PDF 2: cura 料金戦略.pdf
# ============================================================
def generate_pdf2():
    path = os.path.join(OUTPUT_DIR, 'cura 料金戦略.pdf')
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title='cura 料金戦略',
        author='cura',
    )
    styles = get_styles()
    elems = []

    elems += make_header('cura 料金戦略', '確定版（2026年4月）', styles)

    # ============ 基本原則 ============
    elems.append(Paragraph('cura の価格方針', styles['section']))
    principles = [
        '需要 > 供給 → 値上げのタイミング',
        '予約が埋まり始めたら即値上げ',
        '安いは逃げ。高い価格が富裕層への入り口',
    ]
    for p in principles:
        elems.append(Paragraph('・' + p, styles['bullet']))
    elems.append(Spacer(1, 10))

    # ============ 料金ランク比較 ============
    elems.append(Paragraph('料金ランク比較（A案〜C案）', styles['section']))

    rate_data = [
        ['項目', 'A案（最低ライン）', 'B案（ミドル）', 'C案（確定・開業スタート）', '備考'],
        ['プライベートケア', '¥8,800/時', '¥10,000/時', '¥12,000/時', '最低3時間〜'],
        ['看護師同行', '¥16,500/時', '¥18,000/時', '¥18,000/時', '最低3時間〜'],
        ['入会金', '¥33,000', '¥50,000', '¥60,000', '初回のみ'],
        ['夜間オンコール', '¥11,000/月', '¥16,500/月', '¥17,000/月', '月3回まで'],
    ]
    col_widths = [42*mm, 32*mm, 32*mm, 40*mm, 24*mm]
    t = Table(rate_data, colWidths=col_widths)
    ts = standard_table_style()
    add_alternating_rows(ts, len(rate_data))
    # C案列（index=3）をローズ背景でハイライト
    for row in range(1, len(rate_data)):
        ts.add('BACKGROUND', (3, row), (3, row), ROSE_LIGHT)
        ts.add('TEXTCOLOR', (3, row), (3, row), ROSE)
        ts.add('FONTNAME', (3, row), (3, row), FONT_BOLD)
    # C案ヘッダーも強調
    ts.add('BACKGROUND', (3, 0), (3, 0), ROSE)
    ts.add('TEXTCOLOR', (3, 0), (3, 0), WHITE)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 12))

    # ============ なぜC案か ============
    elems.append(Paragraph('なぜC案（¥12,000）で開業するのか', styles['section']))

    reasons = [
        ('富裕層の検索行動',
         '富裕層は「高い順」で検索し、信頼できるサービスを探す。¥8,800・¥10,000は「安価なサービス」と認識され、そもそも検索結果に引っかからない。¥12,000が「プレミアムケア」として見つけてもらえる価格帯。'),
        ('競合との比較',
         '都内の自費看護師サービス（NHC等）は¥11,000〜22,000/時で成立している。curaは介護福祉士＋看護師バックアップのW体制。看護師単体と同価格帯で、より手厚いサービスを提供できる。'),
        ('スタッフへの還元',
         '高単価だからこそ、スタッフに手取り30万円超を払える。安く設定すれば人が集まらず、品質も維持できない。curaの「スタッフ幸福最優先」という理念は、¥12,000あってこそ成立する。'),
        ('有料老人ホームとの比較',
         '富裕層が施設に入ると月30〜50万かかる。curaを月数回利用しても、施設費用より大幅に安く「自宅で最高のケア」が受けられる。この文脈では¥12,000は「安い選択肢」になる。'),
    ]
    for i, (title, body) in enumerate(reasons, 1):
        elems.append(Paragraph(f'{i}. {title}', styles['subsection']))
        elems.append(Paragraph(body, styles['body']))
    elems.append(Spacer(1, 10))

    # ============ 値上げロードマップ ============
    elems.append(Paragraph('値上げロードマップ', styles['section']))
    roadmap = [
        '開業時：¥12,000/時（C案）でスタート',
        '予約が月の7割埋まったら：¥15,000/時を検討',
        'さらに需要が上回ったら：入会金・オンコール料金も見直し',
    ]
    for r in roadmap:
        elems.append(Paragraph('→ ' + r, styles['bullet']))
    elems.append(Spacer(1, 10))

    # ============ 在宅フルサポートプラン ============
    elems.append(Paragraph('在宅フルサポートプランとの整合性', styles['section']))
    full_support = [
        ['項目', '内容'],
        ['内容', '午前2h＋午後2h×毎日＋夜間オンコール'],
        ['計算', '120h × ¥12,000 + ¥17,000 = 月¥1,457,000'],
        ['パッケージ案', '月¥150万ぽっきり（検討中）'],
        ['訴求ポイント', '有料老人ホームとの比較で「在宅の選択肢」として提案'],
    ]
    t = Table(full_support, colWidths=[40*mm, 130*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(full_support))
    t.setStyle(ts)
    elems.append(t)

    # フッター
    elems.append(Spacer(1, 16))
    elems.append(HRFlowable(width='100%', thickness=1, color=GOLD))
    elems.append(Paragraph('更新日：2026年4月　／　cura ／ 文京区千石4-43', styles['note']))

    doc.build(elems)
    print(f'生成完了: {path}')

# ============================================================
# PDF 3: cura 料金検討メモ.pdf
# ============================================================
def generate_pdf3():
    path = os.path.join(OUTPUT_DIR, 'cura 料金検討メモ.pdf')
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title='cura 料金プラン',
        author='cura',
    )
    styles = get_styles()
    elems = []

    elems += make_header('cura 料金プラン', '確定版（2026年4月）', styles)

    # ============ 価格方針 ============
    elems.append(Paragraph('cura の価格方針', styles['section']))
    theory = [
        '富裕層は高い順で検索する',
        '安い＝見つけてもらえない',
        'いいものを安くは終わった',
        '値上げ＝ターゲット層へのシグナル',
    ]
    for t in theory:
        elems.append(Paragraph('・' + t, styles['bullet']))
    elems.append(Spacer(1, 10))

    # ============ 料金ランク比較 ============
    elems.append(Paragraph('料金ランク比較', styles['section']))
    rate_data = [
        ['項目', 'A案', 'B案', 'C案（確定）', '備考'],
        ['プライベートケア', '¥8,800/時', '¥10,000/時', '¥12,000/時', '最低3h'],
        ['看護師同行', '¥16,500/時', '¥18,000/時', '¥18,000/時', '最低3h'],
        ['入会金', '¥33,000', '¥50,000', '¥60,000', '初回のみ'],
        ['夜間オンコール', '¥11,000/月', '¥16,500/月', '¥17,000/月', '月3回まで'],
    ]
    col_widths = [45*mm, 30*mm, 30*mm, 40*mm, 25*mm]
    t = Table(rate_data, colWidths=col_widths)
    ts = standard_table_style()
    add_alternating_rows(ts, len(rate_data))
    for row in range(1, len(rate_data)):
        ts.add('BACKGROUND', (3, row), (3, row), ROSE_LIGHT)
        ts.add('TEXTCOLOR', (3, row), (3, row), ROSE)
        ts.add('FONTNAME', (3, row), (3, row), FONT_BOLD)
    ts.add('BACKGROUND', (3, 0), (3, 0), ROSE)
    ts.add('TEXTCOLOR', (3, 0), (3, 0), WHITE)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 12))

    # ============ なぜC案を選んだか ============
    elems.append(Paragraph('なぜC案を選んだか——5つの根拠', styles['section']))

    reasons = [
        ('富裕層は高い順で検索する',
         '¥8,800は「安価なサービス」のカテゴリに入り、そもそも目に留まらない。ターゲット層に見つけてもらうために、プレミアムな価格帯が必要。'),
        ('競合が証明している',
         'NHCは看護師のみで¥11,000〜22,000/時で成立。curaは介護福祉士＋看護師バックアップ体制で、同価格帯以上の価値を提供できる。'),
        ('スタッフ還元が前提',
         '手取り30万超を払えるのは¥12,000あってこそ。安ければスタッフが集まらず、品質も維持できない。'),
        ('施設との比較優位',
         '有料老人ホームは月30〜50万。curaは「施設に入らず自宅でプレミアムケア」というポジション。この比較では¥12,000/時は安い。'),
        ('開業時から高く設定する',
         '後から値上げするのは難しい。最初から¥12,000で入ることで、顧客層・ブランドイメージが最初から正しく形成される。'),
    ]
    for i, (title, body) in enumerate(reasons, 1):
        elems.append(Paragraph(f'{i}. {title}', styles['subsection']))
        elems.append(Paragraph(body, styles['body']))
    elems.append(Spacer(1, 10))

    # ============ 論点 ============
    elems.append(Paragraph('論点（スタッフ向け説明用）', styles['section']))
    points = [
        '価格の根拠：なぜ¥12,000が適切か（上記5点）',
        'スタッフへの還元：高単価がスタッフ給与を支える',
        '在宅フルサポートプランとの整合性（月¥150万パッケージ）',
    ]
    for i, p in enumerate(points, 1):
        elems.append(Paragraph(f'{i}. ' + p, styles['bullet']))
    elems.append(Spacer(1, 10))

    # ============ 結論 ============
    elems.append(Paragraph('結論', styles['section']))
    # ローズ背景のボックス
    conclusion_data = [['¥12,000/時を開業時スタート価格として確定。実績が積み上がり次第、さらなる値上げを検討する。']]
    t = Table(conclusion_data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ROSE_LIGHT),
        ('TEXTCOLOR', (0, 0), (-1, -1), ROSE),
        ('FONTNAME', (0, 0), (-1, -1), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1.5, ROSE),
    ]))
    elems.append(t)

    # フッター
    elems.append(Spacer(1, 16))
    elems.append(HRFlowable(width='100%', thickness=1, color=GOLD))
    elems.append(Paragraph('更新日：2026年4月　／　cura ／ 文京区千石4-43', styles['note']))

    doc.build(elems)
    print(f'生成完了: {path}')

# ============================================================
# PDF 4: cura_収支v4.pdf
# ============================================================
def generate_pdf4():
    path = os.path.join(OUTPUT_DIR, 'cura_収支v4.pdf')
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=15*mm,
        title='cura 収支シミュレーション',
        author='cura',
    )
    styles = get_styles()
    elems = []

    elems += make_header('cura 収支シミュレーション — 3名体制', '数字はすべて手取りベース', styles)

    # ============ 料金設定 ============
    elems.append(Paragraph('料金設定（確定）', styles['section']))
    rate_data = [
        ['項目', '金額（税込）', '備考'],
        ['プライベートケア（介護福祉士）', '¥12,000/時', '確定・C案'],
        ['看護師同行時給', '¥18,000/時', '同行時のみ発生'],
        ['入会金', '¥60,000', '初回のみ'],
        ['夜間オンコール（月額）', '¥17,000', '加入者のみ・月3回まで'],
    ]
    t = Table(rate_data, colWidths=[75*mm, 45*mm, 50*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(rate_data))
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 8))

    # ============ 料金ランク比較 ============
    elems.append(Paragraph('料金ランク比較（参考）', styles['section']))
    rank_data = [
        ['項目', 'A案', 'B案', 'C案（確定）'],
        ['プライベートケア', '¥8,800/時', '¥10,000/時', '¥12,000/時'],
        ['看護師同行', '¥16,500/時', '¥18,000/時', '¥18,000/時'],
        ['入会金', '¥33,000', '¥50,000', '¥60,000'],
        ['夜間オンコール', '¥11,000/月', '¥16,500/月', '¥17,000/月'],
    ]
    t = Table(rank_data, colWidths=[55*mm, 35*mm, 35*mm, 45*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(rank_data))
    for row in range(1, len(rank_data)):
        ts.add('BACKGROUND', (3, row), (3, row), ROSE_LIGHT)
        ts.add('TEXTCOLOR', (3, row), (3, row), ROSE)
        ts.add('FONTNAME', (3, row), (3, row), FONT_BOLD)
    ts.add('BACKGROUND', (3, 0), (3, 0), ROSE)
    ts.add('TEXTCOLOR', (3, 0), (3, 0), WHITE)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 8))

    # ============ 1件あたり設定 ============
    elems.append(Paragraph('1件あたりの設定（C案ベース）', styles['section']))
    per_case = [
        ['項目', '設定値', '備考'],
        ['1件あたりケア時間', '3時間', '最低3h'],
        ['看護師同行率', '5%', '20件に1件'],
        ['介護士時給（手取り換算）', '¥2,800', '手取り25万 ÷ 稼働想定h'],
        ['看護師時給（業務委託）', '¥2,500', '同行時のみ'],
        ['1件あたり売上', '¥36,900', '(0.95 × ¥36,000) + (0.05 × ¥54,000)'],
        ['1件あたり変動費（人件費）', '¥375', '5% × 3h × ¥2,500'],
        ['1件あたり粗利', '¥36,525', ''],
    ]
    t = Table(per_case, colWidths=[65*mm, 40*mm, 65*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(per_case))
    ts.add('BACKGROUND', (0, len(per_case)-1), (-1, len(per_case)-1), GOLD)
    ts.add('TEXTCOLOR', (0, len(per_case)-1), (-1, len(per_case)-1), WHITE)
    ts.add('FONTNAME', (0, len(per_case)-1), (-1, len(per_case)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 8))

    # ============ 損益分岐点 ============
    elems.append(Paragraph('損益分岐点', styles['section']))
    bep = [
        ['項目', '値'],
        ['固定費合計（実質）', '¥360,000'],
        ['1件あたり粗利', '¥36,525'],
        ['BEP件数', '10件'],
        ['BEP時月売上', '¥369,000'],
    ]
    t = Table(bep, colWidths=[80*mm, 90*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(bep))
    ts.add('BACKGROUND', (0, len(bep)-1), (-1, len(bep)-1), ROSE)
    ts.add('TEXTCOLOR', (0, len(bep)-1), (-1, len(bep)-1), WHITE)
    ts.add('FONTNAME', (0, len(bep)-1), (-1, len(bep)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 8))

    # ============ スタッフ構成 ============
    elems.append(Paragraph('スタッフ構成（軌道乗るまで）', styles['section']))
    staff = [
        ['名前', '役割', '手取り', '雇用形態'],
        ['まさみ', 'ケアディレクター', '20万', '役員'],
        ['看護師', 'メディカルアドバイザー', '5万固定＋歩合', '業務委託'],
        ['キャンちゃん', 'コミュニティMgr', '5万', '業務委託'],
    ]
    t = Table(staff, colWidths=[35*mm, 55*mm, 50*mm, 30*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(staff))
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 8))

    # ============ 月次固定費 ============
    elems.append(Paragraph('月次固定費（手取りベース）', styles['section']))
    fixed = [
        ['項目', '手取り', '備考'],
        ['まさみ役員報酬', '¥200,000', '手取り20万・額面25〜26万'],
        ['看護師固定給', '¥50,000', '業務委託・手取り5万'],
        ['キャンちゃん報酬', '¥50,000', '業務委託・手取り5万'],
        ['賠償責任保険等', '¥30,000', '概算'],
        ['事務所・通信費等', '¥30,000', '概算'],
        ['固定費合計（実質負担）', '¥360,000', ''],
    ]
    t = Table(fixed, colWidths=[65*mm, 40*mm, 65*mm])
    ts = standard_table_style()
    add_alternating_rows(ts, len(fixed))
    ts.add('BACKGROUND', (0, len(fixed)-1), (-1, len(fixed)-1), ROSE)
    ts.add('TEXTCOLOR', (0, len(fixed)-1), (-1, len(fixed)-1), WHITE)
    ts.add('FONTNAME', (0, len(fixed)-1), (-1, len(fixed)-1), FONT_BOLD)
    t.setStyle(ts)
    elems.append(t)
    elems.append(Spacer(1, 8))

    # ============ 損益シミュレーション ============
    elems.append(Paragraph('月次件数別 損益シミュレーション', styles['section']))

    # オンコール売上（5件ごとに2契約追加）
    def oncall(cases):
        contracts = (cases // 5) * 2
        return contracts * 17000

    sim_header = ['件数', 'ケア売上', 'オンコール', '変動費', '粗利', '固定費', '営業利益', '判定']
    sim_data = [sim_header]

    for cases in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
        care_rev = cases * 36900
        oc_rev = oncall(cases)
        var_cost = cases * 375
        gross = care_rev + oc_rev - var_cost
        fixed_cost = 360000
        op_profit = gross - fixed_cost
        verdict = '黒字' if op_profit >= 0 else '赤字'
        sim_data.append([
            f'{cases}件',
            f'¥{care_rev:,}',
            f'¥{oc_rev:,}',
            f'¥{var_cost:,}',
            f'¥{gross:,}',
            f'¥{fixed_cost:,}',
            f'¥{op_profit:,}' if op_profit >= 0 else f'-¥{abs(op_profit):,}',
            verdict,
        ])

    col_widths_sim = [18*mm, 24*mm, 22*mm, 18*mm, 24*mm, 20*mm, 26*mm, 18*mm]
    t = Table(sim_data, colWidths=col_widths_sim)
    ts = standard_table_style()
    add_alternating_rows(ts, len(sim_data))
    # 利益列の色分け（列index=6, 行1〜）
    for i, row_data in enumerate(sim_data[1:], 1):
        verdict = row_data[-1]
        if verdict == '黒字':
            ts.add('TEXTCOLOR', (6, i), (6, i), GREEN)
            ts.add('TEXTCOLOR', (7, i), (7, i), GREEN)
            ts.add('FONTNAME', (6, i), (7, i), FONT_BOLD)
        else:
            ts.add('TEXTCOLOR', (6, i), (6, i), RED)
            ts.add('TEXTCOLOR', (7, i), (7, i), RED)
            ts.add('FONTNAME', (6, i), (7, i), FONT_BOLD)
    # フォントサイズを小さく（tsに追加してからsetStyle）
    ts.add('FONTSIZE', (0, 0), (-1, -1), 8)
    ts.add('TOPPADDING', (0, 0), (-1, -1), 4)
    ts.add('BOTTOMPADDING', (0, 0), (-1, -1), 4)
    t.setStyle(ts)
    elems.append(t)

    # フッター
    elems.append(Spacer(1, 16))
    elems.append(HRFlowable(width='100%', thickness=1, color=GOLD))
    elems.append(Paragraph('cura ／ 文京区千石4-43 ／ 更新：2026年4月', styles['note']))

    doc.build(elems)
    print(f'生成完了: {path}')

# ============================================================
# メイン実行
# ============================================================
if __name__ == '__main__':
    print('PDF生成開始...')
    generate_pdf1()
    generate_pdf2()
    generate_pdf3()
    generate_pdf4()
    print('全PDF生成完了！')
