# Inside SideNavigation class
def connect_filter_logic(self, controller):
    """Wires the tree items to the controller's filter engine."""
    self.tree.itemClicked.connect(lambda item: self.on_item_selected(item, controller))

def on_item_selected(self, item, controller):
    filter_text = item.text(0)
    
    if "Sharp" in filter_text:
        # Trigger filter for sharpness > 70% (Update 1 Logic)
        controller.apply_custom_filter("sharpness_score > 70")
    
    elif "VVIP" in filter_text:
        # Trigger filter for VVIP tags (Update 3 Logic)
        controller.apply_custom_filter("tags LIKE '%#VVIP%'")
        
    elif "Best of Burst" in filter_text:
        # Trigger filter for Burst Heroes (Update 7 Logic)
        controller.apply_custom_filter("tags LIKE '%#BurstHero%'")