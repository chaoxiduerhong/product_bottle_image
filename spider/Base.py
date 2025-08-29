# -*- coding:utf-8 -*-
import json
import traceback
import time
import os
import json
from PIL import Image, ImageDraw, ImageFont

from models import MProducts


class Base:
    """
    瓶子图处理
    源中添加一个字段：processing_img:
    """
    def __init__(self, thread_lock):
        self.mark = None

        self.lock = thread_lock

        self.sysLog = None
        # 测试bid
        self.test_bid = None

    def waiting(self, ts):
        self.sysLog.log(f"Will SLEEP FOR {ts} seconds")
        time.sleep(ts)

    def save(self, data, bid=None):
        pass

    def get_product(self):
        return MProducts.getFirstProduct(self.test_bid)

    def draw_multiline_centered(self, draw, text, font, box_width, x_offset, y, fill="black", line_spacing=4, bold=False):
        """
        自动换行 + 居中绘制
        :param bold: True 时伪加粗（多次描绘）
        """
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            w = draw.textlength(test_line, font=font)
            if w <= box_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for line in lines:
            line_width = draw.textlength(line, font=font)
            x = x_offset + (box_width - line_width) / 2
            if bold:
                # 伪加粗，四个方向 + 原点 多次描绘
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        draw.text((x + dx, y + dy), line, font=font, fill=fill)
            else:
                draw.text((x, y), line, font=font, fill=fill)
            y += font.size + line_spacing
        return y
    
    def create_label_image(self, product):
        """
        创建
        """
        product_name = product['product_name']
        cat_number = f"B{product['bid']}"
        cas_number = f"C{product['cas_no']}"
        output_path = "label.png"

        width, height = 600, 712
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)

        try:
            font_path = "C:/Windows/Fonts/arial.ttf"
            bold_font_path = "C:/Windows/Fonts/arialbd.ttf"

            title_font = ImageFont.truetype(font_path, 46)
            title_font_bold = ImageFont.truetype(bold_font_path, 46)
            normal_font = ImageFont.truetype(font_path, 40)
            bold_font = ImageFont.truetype(bold_font_path, 50)
            small_font = ImageFont.truetype(font_path, 22)

        except:
            title_font = ImageFont.load_default(size=46)
            title_font_bold = ImageFont.load_default(size=46)
            normal_font = ImageFont.load_default(size=40)
            bold_font = ImageFont.load_default(size=50)
            small_font = ImageFont.load_default(size=22)

        margin_x = 30
        box_width = width - 2 * margin_x

        # 计算 Product Name 高度
        def measure_multiline_height(text, font, box_width, line_spacing=4):
            words = text.split(" ")
            lines, current_line = [], ""
            dummy_img = Image.new("RGB", (1, 1))
            dummy_draw = ImageDraw.Draw(dummy_img)
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                w = dummy_draw.textlength(test_line, font=font)
                if w <= box_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            return len(lines) * (font.size + line_spacing)

        """
        总高度计算公式：
        logo高度 + 
        logo距离横线高度 + 
        横线高度 + 
        横线距离标题的高度 + 
        标题高度*行数 + 
        attr1 到标题的高度 + 
        attr1的高度 + 
        attrr2到attr1的高度 + 
        attr2的高度 + 
        attr2到第二个横线的高度 + 
        第二个横线的高度 + 
        footer文字到第二个横线的高度 + 
        footer文字高度
        """
        logo_size = 70
        to_line = 30
        line_h = 2

        logo_h = logo_size  # 60 * 60
        logo_to_line1_h = to_line

        # 配置高度
        line1_h = line_h
        line1_to_product_name_h = to_line
        product_h = measure_multiline_height(product_name, bold_font, box_width)
        product_name_to_attr1_h = 50
        attr1_h = normal_font.size
        attr1_to_attr2_h = 15
        attr2_h = normal_font.size
        attr2_to_line2_h = to_line
        line2_h = line_h
        footer_to_line2_h = to_line
        footer_h = small_font.size

        # 动态计算所有的高度
        content_h = (logo_h + logo_to_line1_h + line1_h +
                     line1_to_product_name_h + product_h + product_name_to_attr1_h +
                     attr1_h + attr1_to_attr2_h + attr2_h + attr2_to_line2_h + line2_h + footer_to_line2_h + footer_h)  # logo + 间距 + 分隔线 + Product + 字段 + 分隔线 + 警告

        # 起始 y 坐标（整体垂直居中）
        start_y = (height - content_h) / 2
        print(start_y)
        # --- Logo ---
        logo = Image.open("logo.png").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        image.paste(logo, (20, int(start_y)))

        # Title 跟logo一条横线
        draw.text((95, int(start_y + (logo_size - title_font.size) / 2)), "BenchChem", fill='black',
                  font=title_font_bold)
        # for dx in [-1, 0, 1]:
        #     for dy in [-1, 0, 1]:
        #         x = 90
        #         y = int(start_y + (logo_size - title_font.size)/2)
        #         draw.text((x + dx, y + dy), "BenchChem", font=title_font, fill="black")
        #         # draw.text((x, int(start_y + (logo_size - title_font.size)/2)), "BenchChem", fill='black', font=title_font)

        # 第一条分隔线  第一条分割线因为logo等缘故，要跟其他边距保持一只需要 -4px
        start_y = start_y + logo_size + logo_to_line1_h + 15
        print(start_y)
        draw.line([(0, start_y), (width, start_y)], fill='black', width=2)

        start_y = start_y + line1_h + line1_to_product_name_h
        print(start_y)
        # Product Name
        start_y = self.draw_multiline_centered(draw, product_name, bold_font, box_width, margin_x, start_y, bold=False)

        start_y = start_y + product_name_to_attr1_h
        print(start_y)
        # CAS / CAT / Batch
        draw.text((margin_x, start_y), f"CAS# {cas_number}", fill='black', font=normal_font)
        draw.text((margin_x + 280, start_y), f"CAT# {cat_number}", fill='black', font=normal_font)

        start_y = start_y + attr1_h + attr1_to_attr2_h
        print(start_y)
        draw.text((margin_x, start_y), f"Batch# {batch_number}", fill='black', font=normal_font)

        # 第二条分隔线
        start_y = start_y + attr2_h + attr2_to_line2_h
        print(start_y)
        draw.line([(0, start_y), (width, start_y)], fill='black', width=2)

        start_y = start_y + line2_h + footer_to_line2_h
        print(start_y)
        # 底部警告
        draw.text((margin_x, start_y), "This product is not intended for human or veterinary use.",
                  fill='black', font=small_font)

        image.save(output_path)
        print(f"标签已保存至: {output_path}")

    def handle(self):
        """
        1. 生成图片
        2. 贴瓶子
        3. 设置存储路径保存图片 + 保存到数据库
        """
        # 创建标签
        
        # 将标签贴到图片上

    def query(self):
        """
        结果表名称： product_ast_bench_outline_detail_{idx}
        """
        is_first = True
        while True:
            try:
                product = None
                if not product:
                    product = self.get_product()

                if not product:
                    msg_content = " 产品已经用尽，请尽快补充产品 "
                    self.sysLog.log(msg_content)
                    self.waiting(600)
                    continue

                # 产品数据检测
                if "bid" not in product:
                    self.sysLog.log("check primary filed failed, next product...")
                    continue

                # 根据产品bid获取其详情：Bid cas product_name 重新构建产品信息

                self.sysLog.log("get product success, bid: %s" % product['bid'])

                self.mark = "[bid:%s]" % (product['bid'])
                self.sysLog.set_mark(self.mark)

                # 生成

                # 保存
                # 1. 更新原来的状态为 success 2. 写入目标表
            except:
                print(traceback.format_exc())
                self.sysLog.err_log(f"未知异常原因，程序等待10分钟再次运行。Error:%s" % traceback.format_exc())
                time.sleep(600)