# -*- coding:utf-8 -*-
import json
import traceback
import time
import os
import json
import cv2
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from spider.logs.syslog import SysLog

from models import MProducts, MProductsResult


class Base:
    """
    瓶子图处理
    源中添加一个字段：processing_img:
    """
    def __init__(self, thread_lock, thread_name):
        self.mark = None
        self.lock = thread_lock
        self.sysLog = SysLog(thread_lock=self.lock)
        self.thread_name = thread_name
        self.lock = thread_lock

        # 测试bid
        self.test_bid = None

    def waiting(self, ts):
        self.sysLog.log(f"Will SLEEP FOR {ts} seconds")
        time.sleep(ts)

    def save(self, data, bid=None):
        pass

    def get_product(self):
        return MProducts.getFirstProduct(self.test_bid)

    def draw_multiline_centered_bak(self, draw, text, font, box_width, x_offset, y, fill="black", line_spacing=4, bold=False):
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
    
    def draw_multiline_centered(self, draw, text, font, box_width, x_offset, y, fill="black", line_spacing=4, bold=False, break_chars="-"):
        """
        自动换行 + 居中绘制，同时支持空格和横向符号换行
        :param break_chars: 横向换行符号，换行时保留在上一行末尾
        :param bold: True 时伪加粗（多次描绘）
        """
        # 分词：空格或 break_chars 都作为分割点，保留 break_chars
        pattern = f'([{"".join(re.escape(c) for c in break_chars)}]|\\s+)'
        tokens = re.split(pattern, text)

        lines = []
        current_line = ""

        for token in tokens:
            if not token:
                continue
            test_line = current_line + token
            w = draw.textlength(test_line, font=font)
            if w <= box_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                # break_char 保留上一行
                if token.strip() in break_chars:
                    current_line = token
                else:
                    current_line = token.lstrip()  # 去掉开头空格

        if current_line:
            lines.append(current_line)

        # 居中绘制
        for line in lines:
            line_width = draw.textlength(line, font=font)
            x = x_offset + (box_width - line_width) / 2
            if bold:
                # 伪加粗，多次描绘
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        draw.text((x + dx, y + dy), line, font=font, fill=fill)
            else:
                draw.text((x, y), line, font=font, fill=fill)
            y += font.size + line_spacing

        return y

    def get_label_path(self, product):
        output_path = f"./storage/labels/label-{product['bid']}.png"
        os.makedirs(os.path.dirname(output_path),  exist_ok=True)
        print(os.path.basename(output_path))
        return output_path


    def create_label_image(self, product):
        """
        创建
        """
        output_path = self.get_label_path(product)
        product_name = product['product_name']
        cat_number = f"B{product['bid']}"
        cas_number = f"{product['cas_no']}"
        molecular_formula = f"{product['molecular_formula']}"
        molecular_weight = f"{product['molecular_weight']}"

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
        def measure_multiline_height_bak(text, font, box_width, line_spacing=4):
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
        
        def measure_multiline_height(text, font, box_width, line_spacing=4, break_chars="-"):
            """
            计算多行文本高度，同时支持空格和自定义横向符号换行。
            
            :param text: 文本字符串
            :param font: PIL ImageFont 对象
            :param box_width: 最大宽度
            :param line_spacing: 行间距
            :param break_chars: 横向换行符号，换行时保留在上一行末尾
            :return: 总高度（像素）
            """
            # 将空格和横向符号都作为分词点
            import re
            # 用正则把空格和 break_chars 都分开，保留 break_chars
            pattern = f'([{"".join(re.escape(c) for c in break_chars)}]|\\s+)'
            tokens = re.split(pattern, text)
            
            lines, current_line = [], ""
            dummy_img = Image.new("RGB", (1, 1))
            dummy_draw = ImageDraw.Draw(dummy_img)
            
            for token in tokens:
                if not token:
                    continue
                # 测试加上当前 token 后的宽度
                test_line = current_line + token
                w = dummy_draw.textlength(test_line, font=font)
                if w <= box_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    # 如果 token 是 break_char，放在上一行末尾
                    if token.strip() in break_chars:
                        current_line = token
                    else:
                        current_line = token.lstrip()  # 去掉开头空格
            if current_line:
                lines.append(current_line)
            
            # 返回总高度
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
        attr_h = 15

        # 配置高度
        line1_h = line_h
        line1_to_product_name_h = to_line
        product_h = measure_multiline_height(product_name, bold_font, box_width)
        product_name_to_attr1_h = 50
        attr1_h = normal_font.size
        attr1_to_attr2_h = attr_h
        attr2_h = normal_font.size
        
        attr2_to_attr3_h = attr_h
        attr3_h = normal_font.size
        
        attr3_to_attr4_h = attr_h
        attr4_h = normal_font.size
        
        attr4_to_line2_h = to_line
        
        line2_h = line_h
        footer_to_line2_h = to_line
        footer_h = small_font.size

        # 第一条横线要比其他的高,额外设置
        line_1_ext_h = 15

        # 动态计算所有的高度
        content_h = (logo_h + logo_to_line1_h + line1_h +
                     line1_to_product_name_h + product_h + product_name_to_attr1_h +
                     attr1_h + attr1_to_attr2_h + 
                     attr2_h + attr2_to_attr3_h + 
                     attr3_h + attr3_to_attr4_h + 
                     attr4_h + attr4_to_line2_h + 
                     line2_h + footer_to_line2_h + footer_h + line_1_ext_h)  # logo + 间距 + 分隔线 + Product + 字段 + 分隔线 + 警告

        # 起始 y 坐标（整体垂直居中）
        start_y = (height - content_h) / 2
        print(start_y)
        # --- Logo ---
        logo = Image.open("logo.png").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        image.paste(logo, (20, int(start_y)))

        # Title 跟logo一条横线
        draw.text((95, int(start_y + (logo_size - title_font.size) / 2)), "BenchChem", fill='black',
                  font=title_font_bold)
        
        # 加粗方案2
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
        # CAS
        draw.text((margin_x, start_y), f"CAS# {cas_number}", fill='black', font=normal_font)
        
        start_y = start_y + attr1_h + attr1_to_attr2_h
        print(start_y)
        draw.text((margin_x, start_y), f"CAT# {cat_number}", fill='black', font=normal_font)

        # molecular_formula
        start_y = start_y + attr2_h + attr2_to_attr3_h
        print(start_y)
        draw.text((margin_x, start_y), f"M. F {molecular_formula}", fill='black', font=normal_font)
        
        # molecular_weight
        start_y = start_y + attr3_h + attr3_to_attr4_h
        print(start_y)
        draw.text((margin_x, start_y), f"M. Wt {molecular_weight}", fill='black', font=normal_font)

        # 第二条分隔线
        start_y = start_y + attr4_h + attr4_to_line2_h
        print(start_y)
        draw.line([(0, start_y), (width, start_y)], fill='black', width=2)

        start_y = start_y + line2_h + footer_to_line2_h
        print(start_y)
        # 底部警告
        draw.text((margin_x, start_y), "This product is not intended for human or veterinary use.",
                  fill='black', font=small_font)

        image.save(output_path)
        print(f"标签已保存至: {output_path}")
        return output_path

    
    def cylindrical_warp(self, label_img, output_size, curvature=1.0):
        """
        将标签图像做圆柱面扭曲映射。

        :param label_img: 输入的标签图 (numpy array)。
        :param output_size: 扭曲后希望得到的输出尺寸 (宽度, 高度)。
        :param curvature: 弧度系数，数值越大，弯曲效果越明显。
        :return: 经过圆柱扭曲后的标签图。
        """
        src_h, src_w = label_img.shape[:2]
        out_h, out_w = output_size[1], output_size[0]

        # 创建映射表
        map_x = np.zeros((out_h, out_w), dtype=np.float32)
        map_y = np.zeros((out_h, out_w), dtype=np.float32)

        # 计算中心点和半径，以确保映射居中
        center_x = src_w / 2

        # 定义弯曲的角度范围
        angle_range = np.pi * curvature / 2

        for y in range(out_h):
            for x in range(out_w):
                # 1. 将输出坐标 x (0 to out_w) 映射到角度 (-angle_range/2 to angle_range/2)
                theta = (x / out_w - 0.5) * angle_range

                # 2. 使用 sin(theta) 计算在源图像中的 x 坐标
                # 将 sin(theta) 从 [-sin(angle/2), sin(angle/2)] 映射回 [0, src_w]
                norm_sin = (np.sin(theta) / np.sin(angle_range / 2) + 1) / 2
                src_x = norm_sin * src_w

                # 3. y 坐标进行线性拉伸
                src_y = (y / out_h) * src_h

                map_x[y, x] = src_x
                map_y[y, x] = src_y

        # 使用 INTER_LINEAR 提供平滑的插值效果
        # 使用 BORDER_REPLICATE 避免因浮点精度问题在边缘产生黑边
        warped = cv2.remap(label_img, map_x, map_y,
                        interpolation=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REPLICATE)
        return warped


    def overlay_image(self, background, overlay, position):
        """
        将一个图像叠加到另一个图像上。
        此函数会自动处理白色背景（使其透明）。

        :param background: 背景图 (瓶子)。
        :param overlay: 前景图 (扭曲后的标签)。
        :param position: 前景图在背景图上的左上角坐标 (x, y)。
        :return: 合成后的图像。
        """
        x, y = position
        bg_h, bg_w = background.shape[:2]
        fg_h, fg_w = overlay.shape[:2]

        # 确定叠加区域 (Region of Interest, ROI)
        if x >= bg_w or y >= bg_h:
            return background

        # 叠加区域的实际尺寸，防止超出边界
        w = min(fg_w, bg_w - x)
        h = min(fg_h, bg_h - y)

        if w <= 0 or h <= 0:
            return background

        # 截取前景和背景的对应区域
        roi = background[y:y+h, x:x+w]
        overlay_resized = overlay[:h, :w]

        # --- 创建蒙版 (Mask) ---
        # 将叠加图转换为灰度图
        gray_overlay = cv2.cvtColor(overlay_resized, cv2.COLOR_BGR2GRAY)

        # 创建蒙版：将接近白色的区域视为透明
        # threshold 值可以调整，240 表示灰度值高于 240 的都算作背景
        _, mask = cv2.threshold(gray_overlay, 240, 255, cv2.THRESH_BINARY_INV)

        # 使用蒙版反转获取背景区域
        mask_inv = cv2.bitwise_not(mask)

        # 从 ROI 中抠出标签形状的区域
        bg_part = cv2.bitwise_and(roi, roi, mask=mask_inv)

        # 获取标签内容区域
        fg_part = cv2.bitwise_and(overlay_resized, overlay_resized, mask=mask)

        # 将两部分相加，完成叠加
        background[y:y+h, x:x+w] = cv2.add(bg_part, fg_part)

        return background

    
    def chem_name_to_url(self, name: str) -> str:
        # 把非字母和非横线的字符替换成下划线
        return re.sub(r'[^a-zA-Z0-9\-]', '_', name).lower()
    
    def get_bottle_name(self, product):
        return f"b{product['bid']}-{self.chem_name_to_url(product['product_name'])}.png"
    
    def get_bottle_path(self, product):
        output_path = f"./storage/bottle/{self.get_bottle_name(product)}"
        os.makedirs(os.path.dirname(output_path),  exist_ok=True)
        return output_path

    def stick_label(self, label_path, product):
        """
        贴图
        """

        bottle_path = "bottle.png"     # 瓶子图片路径 (尺寸 385x700)
        
        output_path =  self.get_bottle_path(product) # 输出结果图片路径

        # --- 参数设置 (你可以调整这些值来改变最终效果) ---

        # 1. 标签在瓶身上的最终尺寸 (宽度, 高度)
        # 这个尺寸决定了标签在瓶身上看起来有多大

        # 透明瓶子
        # final_label_size = (330, 392)

        # 棕色瓶子
        final_label_size = (580, 688)

        # 2. 标签在瓶身上的位置 (左上角坐标 x, y)
        # x: 离瓶子左边的距离
        # y: 离瓶子顶部的距离

        # 透明瓶子
        # position_on_bottle = (27, 336)

        # 棕色瓶子
        position_on_bottle = (30, 570)

        # 3. 标签的弯曲程度
        # 1.0 是一个比较自然的效果。可以增大或减小来改变弯曲度。
        curvature = 1.0

        # --- 执行步骤 ---

        # 1. 读取图片
        print("正在读取图片...")
        if not os.path.exists(bottle_path) or not os.path.exists(label_path):
            print(f"错误：请确保 '{bottle_path}' 和 '{label_path}' 文件存在于当前目录中。")
        else:
            bottle_img = cv2.imread(bottle_path)
            label_img = cv2.imread(label_path)

            # 2. 对标签进行圆柱形扭曲
            print("正在对标签进行扭曲...")
            warped_label = self.cylindrical_warp(label_img, final_label_size, curvature)

            # 3. 将扭曲后的标签贴到瓶子上
            print("正在将标签叠加到瓶子上...")
            result_img = self.overlay_image(bottle_img.copy(), warped_label, position_on_bottle)

            # 4. 保存结果
            cv2.imwrite(output_path, result_img)
            print(f"处理完成！结果已保存到: {output_path}")
        return output_path

            
            
    
    def handle(self, product):
        """
        1. 生成图片
        2. 贴瓶子
        3. 设置存储路径保存图片 + 保存到数据库
        """
        # 创建标签
        try:
            lable_path = self.create_label_image(product)
            # 检测标签是否存在了,存在则创建成功了
            if not os.path.exists(lable_path):
                return {
                    "label_path": "",
                    "bottle_path": "",
                    "bottle_name": "",
                    "status": "failed",
                    "error": "lable_path_error",
                }
            
            self.sysLog.log("标签生成成功")
            
            # 将标签贴到图片上
            bottle_path = self.stick_label(lable_path, product)
            if not os.path.exists(lable_path):
                return {
                    "label_path": "",
                    "bottle_path": "",
                    "bottle_name": "",
                    "status": "failed",
                    "error": "stick_label_error",
                }
            
            return {
                "label_path": lable_path,
                "bottle_path": bottle_path,
                "bottle_name": f"{self.get_bottle_name(product)}",
                "status": "success",
                "error": "error",
            }
            
        except:
            print(traceback.format_exc())
            return {
                "label_path": "",
                "bottle_path": "",
                "bottle_name": "",
                "status": "failed",
                "error": "error"
            }
        

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

                self.mark = "[bid:%s][thread_name: %s]" % (product['bid'], self.thread_name)
                self.sysLog.set_mark(self.mark)
            
                # 生成
                result = self.handle(product)

                # 保存
                result['bid'] = product['bid']
                result['porduct_name'] = product['product_name']
                exists = MProductsResult.total(condition={"bid": product['bid']})
                if exists:
                    MProductsResult.update_one(data=result, condition={
                        "bid": product['bid']
                    })
                else:
                    MProductsResult.add_one(data=result)
                
                # 更新队列状态
                image_processing = "success" if result['status'] == "success" else "failed"
                MProducts.update_one(condition={
                    "bid": product['bid']
                }, data= {"image_processing": image_processing})
                
                self.sysLog.log("save success ,next product...")

                # 保存
                # 1. 更新原来的状态为 success 2. 写入目标表
            except:
                print(traceback.format_exc())
                self.sysLog.err_log(f"未知异常原因，程序等待10分钟再次运行。Error:%s" % traceback.format_exc())
                time.sleep(600)