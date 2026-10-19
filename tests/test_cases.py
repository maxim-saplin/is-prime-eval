from collections import Counter
import unittest

from cases import Case, COMPOSITE, PRIME, generate_cases, is_prime


class PrimalityOracleTests(unittest.TestCase):
    def test_is_prime_is_exact_for_supported_examples(self):
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(1))
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(97))
        self.assertTrue(is_prime(1_000_000_007))
        self.assertFalse(is_prime(100))
        self.assertFalse(is_prime(9_999_999_999))

    def test_is_prime_rejects_out_of_contract_inputs(self):
        with self.assertRaises(TypeError):
            is_prime(True)
        with self.assertRaises(TypeError):
            is_prime(3.0)
        with self.assertRaises(ValueError):
            is_prime(10**10)

    def test_is_prime_matches_sieve_for_small_values(self):
        limit = 10_000
        expected = [True] * limit
        expected[0:2] = [False, False]
        for candidate in range(2, int((limit - 1) ** 0.5) + 1):
            if expected[candidate]:
                for multiple in range(candidate * candidate, limit, candidate):
                    expected[multiple] = False
        for number, expected_label in enumerate(expected):
            with self.subTest(number=number):
                self.assertEqual(is_prime(number), expected_label)


class CaseGenerationTests(unittest.TestCase):
    def test_generate_cases_is_balanced_unique_and_well_formed(self):
        cases = generate_cases(depths=[4, 5], samples_per_class=4, seed=12345)

        self.assertEqual(len(cases), 16)
        self.assertTrue(all(isinstance(case, Case) for case in cases))
        self.assertEqual(
            Counter((case.depth, case.label) for case in cases),
            {
                (4, PRIME): 4,
                (4, COMPOSITE): 4,
                (5, PRIME): 4,
                (5, COMPOSITE): 4,
            },
        )
        self.assertEqual(len({case.number for case in cases}), len(cases))
        self.assertEqual(len({case.case_id for case in cases}), len(cases))
        for case in cases:
            self.assertGreaterEqual(case.number, 10 ** (case.depth - 1))
            self.assertLessEqual(case.number, 10**case.depth - 1)
            self.assertEqual(len(str(case.number)), case.depth)
            self.assertEqual(case.case_id, f"d{case.depth}-{case.number}")
            self.assertEqual(case.label == PRIME, is_prime(case.number))

    def test_generate_cases_is_reproducible_for_a_seed(self):
        args = ([4, 6], 3, 2026)
        self.assertEqual(generate_cases(*args), generate_cases(*args))

    def test_generate_cases_validates_arguments(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            generate_cases([], samples_per_class=1, seed=1)
        with self.assertRaisesRegex(ValueError, "duplicates"):
            generate_cases([4, 4], samples_per_class=1, seed=1)
        with self.assertRaisesRegex(ValueError, "between 1 and 10"):
            generate_cases([11], samples_per_class=1, seed=1)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            generate_cases([4], samples_per_class=0, seed=1)
        with self.assertRaisesRegex(TypeError, "seed"):
            generate_cases([4], samples_per_class=1, seed="1")


if __name__ == "__main__":
    unittest.main()
