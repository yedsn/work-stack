import threading
import unittest
import uuid

from utils.single_instance import SingleInstanceManager


class SingleInstanceManagerTests(unittest.TestCase):
    def setUp(self):
        self.change_app_id()

    def tearDown(self):
        # Ensure no dangling lock remains between tests
        if hasattr(self, "primary_manager") and self.primary_manager:
            self.primary_manager.release()
            self.primary_manager = None

    def change_app_id(self):
        self.app_id = f"work-stack-test-{uuid.uuid4().hex}"
        self.primary_manager = None

    def test_acquire_blocks_second_instance_until_release(self):
        self.primary_manager = SingleInstanceManager(app_id=self.app_id)
        other_manager = SingleInstanceManager(app_id=self.app_id)

        self.assertTrue(self.primary_manager.acquire(lambda: None))
        self.assertFalse(other_manager.acquire(lambda: None))

        self.primary_manager.release()
        self.primary_manager = None
        self.assertTrue(other_manager.acquire(lambda: None))
        other_manager.release()

    def test_activation_request_notifies_primary(self):
        activation_event = threading.Event()
        self.primary_manager = SingleInstanceManager(app_id=self.app_id)
        self.assertTrue(self.primary_manager.acquire(activation_event.set))

        duplicate = SingleInstanceManager(app_id=self.app_id)
        # Duplicate acquisition should fail while active
        self.assertFalse(duplicate.acquire(lambda: None))
        self.assertTrue(duplicate.activate_existing())
        self.assertTrue(activation_event.wait(timeout=1.0))


if __name__ == "__main__":
    unittest.main()
