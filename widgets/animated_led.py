"""
Animated LED Widget
Custom Canvas widget dengan animasi LED realistis
"""

import tkinter as tk
import math


class AnimatedLED(tk.Canvas):
    """Canvas widget dengan animasi LED yang realistis"""
    
    def __init__(self, parent, size=100, **kwargs):
        """
        Initialize LED widget
        
        Args:
            parent: Parent widget
            size: Ukuran LED dalam pixel
        """
        super().__init__(parent, width=size, height=size, 
                        bg="#0d1117", highlightthickness=0, **kwargs)
        self.size = size
        self.state = False
        self.animation_step = 0
        self._draw_led()
    
    def _draw_led(self):
        """Draw all LED layers"""
        center = self.size // 2
        
        # Outer glow (animated)
        self.glow_outer = self.create_oval(
            5, 5, self.size-5, self.size-5,
            fill="#1a1a2e", outline="", tags="glow"
        )
        
        # Middle glow
        self.glow_middle = self.create_oval(
            15, 15, self.size-15, self.size-15,
            fill="#16213e", outline="", tags="glow"
        )
        
        # Main LED body
        self.led_body = self.create_oval(
            25, 25, self.size-25, self.size-25,
            fill="#2d3748", outline="#4a5568", width=2
        )
        
        # Inner highlight
        self.highlight = self.create_oval(
            30, 30, center-5, center-5,
            fill="#374151", outline=""
        )
        
        # Center dot
        self.center_dot = self.create_oval(
            center-8, center-8, center+8, center+8,
            fill="#1f2937", outline=""
        )
    
    def set_state(self, on: bool, color="#00ff7f"):
        """
        Set LED on/off dengan warna
        
        Args:
            on: True untuk ON, False untuk OFF
            color: Hex color untuk LED saat ON
        """
        self.state = on
        if on:
            self.animate_on(color)
        else:
            self.animate_off()
    
    def animate_on(self, color):
        """Animate LED turning ON"""
        self.itemconfig(self.glow_outer, fill=self._adjust_brightness(color, 0.3))
        self.itemconfig(self.glow_middle, fill=self._adjust_brightness(color, 0.5))
        self.itemconfig(self.led_body, fill=color, outline=color)
        self.itemconfig(self.highlight, fill=self._adjust_brightness(color, 1.5))
        self.itemconfig(self.center_dot, fill=self._adjust_brightness(color, 1.8))
        self._pulse()
    
    def animate_off(self):
        """Animate LED turning OFF"""
        self.itemconfig(self.glow_outer, fill="#1a1a2e")
        self.itemconfig(self.glow_middle, fill="#16213e")
        self.itemconfig(self.led_body, fill="#2d3748", outline="#4a5568")
        self.itemconfig(self.highlight, fill="#374151")
        self.itemconfig(self.center_dot, fill="#1f2937")
    
    def _pulse(self):
        """Create pulsing glow effect"""
        if not self.state:
            return
        
        scale = 1 + 0.1 * math.sin(self.animation_step * 0.3)
        self.animation_step += 1
        
        if self.animation_step % 30 == 0:
            self.animation_step = 0
        
        self.after(50, self._pulse)
    
    def _adjust_brightness(self, hex_color, factor):
        """
        Adjust brightness of hex color
        
        Args:
            hex_color: Color in hex format (#RRGGBB)
            factor: Brightness factor (>1 brighter, <1 darker)
        
        Returns:
            Adjusted hex color
        """
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        
        return f'#{r:02x}{g:02x}{b:02x}'
