overlap = 0.001;
dovetail_bottom = 4;
dovetail_negative_scale = 1.02;
strip_width = 10;
led_spacing = 16.54;
panel_thickness = 2;
pixels = 8;

module dovetail(scale=1, height=panel_thickness+2*overlap) {
    length = 2 * scale;
    top = 5 * scale;
    bottom = 4 * scale;
    linear_extrude(height=height)
        polygon(points=[
            [0, 0],
            [length, (top-bottom)/2],
            [length, -(bottom + (top-bottom)/2)],
            [0, -bottom]
        ]);
}

for (i = [0 : pixels-1]) {
    translate([0, i*led_spacing, 0])
        difference() {
            cube([pixels * led_spacing, led_spacing, panel_thickness]);
            translate([-overlap, (led_spacing - strip_width + dovetail_bottom * dovetail_negative_scale) / 2, -overlap])
                dovetail(scale=dovetail_negative_scale);
        };
    
    translate([pixels * led_spacing-overlap, (led_spacing - strip_width + dovetail_bottom) / 2 + i*led_spacing, -overlap])
                dovetail(scale=1);
    
    translate([0, i*led_spacing, panel_thickness-overlap])
        cube([pixels * led_spacing, led_spacing-strip_width, panel_thickness/2]);
}

difference() {
    translate([0, pixels*led_spacing, 0])
        cube([pixels * led_spacing, led_spacing-strip_width, panel_thickness*1.5]);
    translate([-overlap, (led_spacing - strip_width + dovetail_bottom * dovetail_negative_scale) / 2 + pixels*led_spacing, -overlap])
        dovetail(scale=dovetail_negative_scale);
}

translate([pixels * led_spacing-overlap, (led_spacing - strip_width + dovetail_bottom) / 2 + pixels*led_spacing, -overlap])
    dovetail(scale=1);
