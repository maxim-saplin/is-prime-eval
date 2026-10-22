from collections import Counter
import unittest

from is_prime_eval.cases import (
    CASE_GENERATOR_VERSION,
    Case,
    COMPOSITE,
    PRIME,
    generate_cases,
    generate_supplemental_cases,
    is_prime,
)


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
            is_prime(10**15)

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

    def test_deterministic_miller_rabin_rejects_strong_pseudoprimes(self):
        self.assertFalse(is_prime(341_550_071_728_321))
        self.assertFalse(is_prime(382_512_305_654_641))
        self.assertTrue(is_prime(999_999_999_999_989))  # known 15-digit prime
        self.assertFalse(is_prime(2**47 - 1))  # composite Mersenne number
        self.assertFalse(is_prime(10**15 - 1))


class CaseGenerationTests(unittest.TestCase):
    def test_generator_version_is_stable(self):
        self.assertEqual(CASE_GENERATOR_VERSION, "v1")

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

    def test_supplemental_cases_are_disjoint_balanced_and_reproducible(self):
        parent = generate_cases(range(4, 11), samples_per_class=10, seed=2026)
        first = generate_supplemental_cases(
            parent,
            target_depth=15,
            existing_depths_per_class=5,
            new_depths_per_class=15,
            seed=88421,
        )
        second = generate_supplemental_cases(
            parent,
            target_depth=15,
            existing_depths_per_class=5,
            new_depths_per_class=15,
            seed=88421,
        )
        self.assertEqual(first, second)
        top_up, new_depths = first
        self.assertEqual(len(top_up), 7 * 2 * 5)
        self.assertEqual(len(new_depths), 5 * 2 * 15)
        parent_pairs = {(case.depth, case.number) for case in parent}
        extension_pairs = {(case.depth, case.number) for case in top_up + new_depths}
        self.assertEqual(len(extension_pairs), len(top_up) + len(new_depths))
        self.assertFalse(parent_pairs & extension_pairs)
        self.assertEqual(
            Counter((case.depth, case.label) for case in top_up),
            {(depth, label): 5 for depth in range(4, 11) for label in (PRIME, COMPOSITE)},
        )
        self.assertEqual(
            Counter((case.depth, case.label) for case in new_depths),
            {(depth, label): 15 for depth in range(11, 16) for label in (PRIME, COMPOSITE)},
        )

    def test_extension_generation_preserves_seeded_depth_4_to_10_cases_and_hash(self):
        from is_prime_eval.runner import _case_record, _sha256

        base_depths = tuple(range(4, 11))
        target_depths = tuple(range(4, 16))
        base = generate_cases(base_depths, samples_per_class=10, seed=2026)
        target = generate_cases(target_depths, samples_per_class=10, seed=2026)
        target_prefix = [case for case in target if case.depth <= 10]
        self.assertEqual(target_prefix, base)
        payload = {
            "schema_version": 1,
            "generator_version": CASE_GENERATOR_VERSION,
            "seed": 2026,
            "depths": list(base_depths),
            "samples_per_class": 10,
            "cases": [_case_record(case) for case in base],
        }
        self.assertEqual(
            _sha256(payload),
            "fc48a8ff5cee2be50fc87f51916018fba9bb856ea28b3616edfc734e7ebd9652",
        )
        extra = [case for case in target if case.depth > 10]
        self.assertEqual({case.depth for case in extra}, set(range(11, 16)))
        self.assertEqual(len(extra), 100)

    def test_generate_cases_validates_arguments(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            generate_cases([], samples_per_class=1, seed=1)
        with self.assertRaisesRegex(ValueError, "duplicates"):
            generate_cases([4, 4], samples_per_class=1, seed=1)
        with self.assertRaisesRegex(ValueError, "between 1 and 15"):
            generate_cases([16], samples_per_class=1, seed=1)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            generate_cases([4], samples_per_class=0, seed=1)
        with self.assertRaisesRegex(TypeError, "seed"):
            generate_cases([4], samples_per_class=1, seed="1")


if __name__ == "__main__":
    unittest.main()
