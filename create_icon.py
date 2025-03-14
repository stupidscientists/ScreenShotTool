"""
创建图标脚本
用于生成应用程序图标
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    """
    创建应用程序图标
    """
    print("创建应用程序图标...")
    
    # 创建一个512x512的透明背景图像
    icon_size = 512
    icon = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制一个圆形背景
    circle_color = (76, 175, 80, 230)  # 绿色，半透明
    circle_radius = icon_size // 2 - 10
    circle_center = (icon_size // 2, icon_size // 2)
    draw.ellipse(
        (
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius
        ),
        fill=circle_color
    )
    
    # 绘制一个相机图标
    camera_color = (255, 255, 255, 255)  # 白色
    camera_width = int(icon_size * 0.6)
    camera_height = int(camera_width * 0.7)
    camera_left = (icon_size - camera_width) // 2
    camera_top = (icon_size - camera_height) // 2
    
    # 相机主体
    draw.rectangle(
        (
            camera_left,
            camera_top,
            camera_left + camera_width,
            camera_top + camera_height
        ),
        fill=camera_color,
        outline=(50, 50, 50, 255),
        width=3
    )
    
    # 相机镜头
    lens_radius = int(camera_width * 0.25)
    lens_center = (icon_size // 2, icon_size // 2)
    draw.ellipse(
        (
            lens_center[0] - lens_radius,
            lens_center[1] - lens_radius,
            lens_center[0] + lens_radius,
            lens_center[1] + lens_radius
        ),
        fill=(50, 50, 50, 255),
        outline=(30, 30, 30, 255),
        width=2
    )
    
    # 相机闪光灯
    flash_radius = int(camera_width * 0.08)
    flash_center = (camera_left + int(camera_width * 0.2), camera_top + int(camera_height * 0.3))
    draw.ellipse(
        (
            flash_center[0] - flash_radius,
            flash_center[1] - flash_radius,
            flash_center[0] + flash_radius,
            flash_center[1] + flash_radius
        ),
        fill=(255, 240, 200, 255)
    )
    
    # 保存为PNG
    png_path = "icon.png"
    icon.save(png_path)
    print(f"PNG图标已保存: {png_path}")
    
    # 保存为ICO
    try:
        ico_path = "icon.ico"
        # 创建不同尺寸的图标
        sizes = [16, 32, 48, 64, 128, 256]
        icons = []
        for size in sizes:
            icons.append(icon.resize((size, size), Image.LANCZOS))
        
        # 保存为ICO文件
        icons[0].save(
            ico_path,
            format='ICO',
            sizes=[(i.width, i.height) for i in icons],
            append_images=icons[1:]
        )
        print(f"ICO图标已保存: {ico_path}")
        return ico_path
    except Exception as e:
        print(f"创建ICO图标时出错: {e}")
        print("将使用PNG图标")
        return png_path

if __name__ == "__main__":
    create_icon() 