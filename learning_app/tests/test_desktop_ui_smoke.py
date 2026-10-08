import os
import unittest

from learning_app.app import LearningApp


@unittest.skipUnless(os.name == "nt" or os.environ.get("DISPLAY"), "GUI smoke test requires a desktop display")
class DesktopUiSmokeTests(unittest.TestCase):
    def test_window_constructs_with_sequential_learning_path(self):
        app = LearningApp()
        try:
            app.withdraw()
            app.update_idletasks()
            self.assertEqual(app.active_type, "Lettera di incarico")
            self.assertEqual(app.step_list.size(), len(app.step_states))
            self.assertEqual(app.step_states[app.active_type], "Da raccogliere")
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
