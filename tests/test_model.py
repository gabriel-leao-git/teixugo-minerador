import unittest

from _helpers import example_brief, example_report
from tx import model


class ReportValidation(unittest.TestCase):
    def test_example_is_valid(self):
        errors, warnings = model.validate_report(example_report())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_verified_requires_source_and_date(self):
        r = example_report()
        del r["products"][0]["engagement"]["source"]
        del r["products"][0]["engagement"]["date"]
        errors, _ = model.validate_report(r)
        self.assertTrue(any("engagement" in e and "source" in e for e in errors))
        self.assertTrue(any("engagement" in e and "date" in e for e in errors))

    def test_hypothesis_mode_rejects_verified_data(self):
        r = example_report()
        r["meta"]["mode"] = "hypothesis"
        errors, _ = model.validate_report(r)
        self.assertTrue(any("hypothesis" in e for e in errors))

    def test_missing_required_field(self):
        r = example_report()
        del r["products"][1]["supplier"]
        errors, _ = model.validate_report(r)
        self.assertTrue(any("products[1].supplier" in e for e in errors))

    def test_top_post_must_be_url_when_verified(self):
        r = example_report()
        r["products"][0]["top_post"]["value"] = "um link qualquer"
        errors, _ = model.validate_report(r)
        self.assertTrue(any("URL" in e for e in errors))

    def test_unverified_top_post_may_be_text(self):
        r = example_report()
        r["products"][0]["top_post"] = {"value": "não verificado", "label": "unverified"}
        errors, _ = model.validate_report(r)
        self.assertEqual(errors, [])

    def test_duplicate_product_name(self):
        r = example_report()
        r["products"][1]["name"] = r["products"][0]["name"]
        errors, _ = model.validate_report(r)
        self.assertTrue(any("duplicado" in e for e in errors))

    def test_same_solution_type_warns(self):
        r = example_report()
        for p in r["products"]:
            p["solution_type"] = "Luva"
        _, warnings = model.validate_report(r)
        self.assertTrue(any("solution_type" in w for w in warnings))

    def test_quantity_mismatch_warns(self):
        r = example_report()
        r["meta"]["quantity"] = 5
        _, warnings = model.validate_report(r)
        self.assertTrue(any("quantity" in w for w in warnings))

    def test_bad_date_and_label(self):
        r = example_report()
        r["products"][0]["segment"]["date"] = "05/10/2026"
        r["products"][0]["target_audience"]["label"] = "certeza"
        errors, _ = model.validate_report(r)
        self.assertTrue(any("segment.date" in e for e in errors))
        self.assertTrue(any("target_audience.label" in e for e in errors))

    def test_economics_requires_positive_price(self):
        r = example_report()
        r["products"][0]["economics"]["price"] = 0
        errors, _ = model.validate_report(r)
        self.assertTrue(any("economics.price" in e for e in errors))

    def test_not_an_object(self):
        self.assertTrue(model.validate_report([])[0])


class BriefValidation(unittest.TestCase):
    def test_example_is_valid(self):
        errors, _, out = model.validate_brief(example_brief())
        self.assertEqual(errors, [])
        self.assertEqual(out["quantity"], 3)

    def test_defaults_applied(self):
        errors, _, out = model.validate_brief({"pain": "remover pelo de cachorro"})
        self.assertEqual(errors, [])
        self.assertEqual(out["market"], ["BR"])
        self.assertEqual(out["rank_by"], ["social", "search"])
        self.assertEqual(out["output_formats"], ["md"])

    def test_pain_is_required(self):
        errors, _, _ = model.validate_brief({"quantity": 3})
        self.assertTrue(any("pain" in e for e in errors))

    def test_invalid_values(self):
        errors, _, _ = model.validate_brief(
            {"pain": "x", "quantity": 0, "output_formats": ["gif"], "rank_by": ["sorte"], "language": "fr"}
        )
        self.assertEqual(len([e for e in errors if e.split(":")[0] in ("quantity", "output_formats", "rank_by", "language")]), 4)


class Helpers(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(model.slugify("Remover pelo de cachorro!"), "remover-pelo-de-cachorro")
        self.assertEqual(model.slugify("???"), "relatorio")

    def test_is_date(self):
        self.assertTrue(model.is_date("2026-10-05"))
        self.assertFalse(model.is_date("2026-13-40"))
        self.assertFalse(model.is_date(20261005))


if __name__ == "__main__":
    unittest.main()
