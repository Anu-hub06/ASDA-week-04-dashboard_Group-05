# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.3.0",
#     "marimo>=0.25.2",
#     "openpyxl==3.1.5",
#     "pandas==3.1.1",
#     "pingouin==0.7.0",
# ]
# ///
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import pingouin as pg

    return alt, mo, pd, pg


@app.cell
def _(pd):
    base_url = "https://docs.google.com/spreadsheets/d/"
    doc_id = "1JfN7vBpVewr7uvYhm4GltBHQiBmSMyJkvTWT2rMqMko/"
    mode = "export/format=excel"

    url = base_url + doc_id + mode

    gsheet = pd.ExcelFile(url)
    mat_df = gsheet.parse("mat")
    por_df = gsheet.parse("por")
    return mat_df, por_df


@app.cell
def _(mat_df, pd, por_df):
    #Merge Math and Portuguese datasets

    key_cols = [
        "school", "sex", "age", "address", "famsize", "Pstatus",
        "Medu", "Fedu", "Mjob", "Fjob", "reason", "nursery", "internet"
    ]

    grade_cols = ["G1", "G2", "G3"]

    df_merged = pd.merge(
        mat_df[key_cols + grade_cols],
        por_df[key_cols + grade_cols],
        on=key_cols,
        how="inner",
        suffixes=("_mat", "_por")
    )
    return (df_merged,)


@app.cell
def _(df_merged, mat_df, por_df):
    #Clean datasets and convert category values into readable labels

    def clean_df(df, merged=False):

        schools = {
            "GP": "Gabriel Pereira",
            "MS": "Mousinho da Silveira"
        }

        sexes = {
            "F": "female",
            "M": "male"
        }

        famsizes = {
            "LE3": "3 or fewer",
            "GT3": "More than 3"
        }

        df = df.assign(
            school=df["school"].map(schools),
            sex=df["sex"].map(sexes),
            famsize=df["famsize"].map(famsizes)
        )

        if merged:
            relevant_cols = ["school", "sex", "famsize", "G3_mat", "G3_por"]
        else:
            relevant_cols = ["school", "sex", "famsize", "G3"]

        return df[relevant_cols]


    mat_clean_df = clean_df(mat_df)
    por_clean_df = clean_df(por_df)
    both_clean_df = clean_df(df_merged, merged=True)
    return both_clean_df, mat_clean_df, por_clean_df


@app.cell
def _(mat_clean_df, mo):
    #Create interactive dashboard filters

    sex = mo.ui.dropdown(
        options=["both"] + sorted(mat_clean_df["sex"].unique().tolist()),
        value="both",
        label="Sex"
    )

    school = mo.ui.dropdown(
        options=["both"] + sorted(mat_clean_df["school"].unique().tolist()),
        value="both",
        label="School"
    )

    famsize = mo.ui.dropdown(
        options=["both"] + sorted(mat_clean_df["famsize"].unique().tolist()),
        value="both",
        label="Family size"
    )

    subject = mo.ui.radio(
        options=["math", "portuguese", "both"],
        value="both",
        label="Subject"
    )
    return famsize, school, sex, subject


@app.cell
def _(
    both_clean_df,
    famsize,
    mat_clean_df,
    por_clean_df,
    school,
    sex,
    subject,
):
    # Apply selected filters to the datasets

    if subject.value == "math":
        filtered_df = mat_clean_df.copy()
        grade_column = "G3"
        subject_label = "Math"

    elif subject.value == "portuguese":
        filtered_df = por_clean_df.copy()
        grade_column = "G3"
        subject_label = "Portuguese"

    else:
        filtered_df = both_clean_df.copy()
        grade_column = None
        subject_label = "Math and Portuguese"

    if sex.value != "both":
        filtered_df = filtered_df[filtered_df["sex"] == sex.value]

    if school.value != "both":
        filtered_df = filtered_df[filtered_df["school"] == school.value]

    if famsize.value != "both":
        filtered_df = filtered_df[filtered_df["famsize"] == famsize.value]
    return filtered_df, grade_column, subject_label


@app.cell
def _(filtered_df, grade_column, subject, subject_label):
    ##Prepare data for the histogram

    if subject.value == "both":
        plot_df = filtered_df.melt(
            id_vars=["school", "sex", "famsize"],
            value_vars=["G3_mat", "G3_por"],
            var_name="subject",
            value_name="G3"
        )

        plot_df["subject"] = plot_df["subject"].map({
            "G3_mat": "Math",
            "G3_por": "Portuguese"
        })

    else:
        plot_df = filtered_df.rename(
            columns={grade_column: "G3"}
        ).copy()

        plot_df["subject"] = subject_label
    return (plot_df,)


@app.cell
def _(alt, filtered_df, plot_df, subject_label):
    ## Interactive histogram of final grades

    chart = alt.Chart(plot_df).mark_bar(
        opacity=0.7
    ).encode(
        x=alt.X(
            "G3:Q",
            bin=alt.Bin(step=1),
            title="Final grade (G3)"
        ),
        y=alt.Y(
            "count():Q",
            title="Number of students"
        ),
        color=alt.Color(
            "subject:N",
            title="Subject"
        ),
        tooltip=[
            alt.Tooltip("G3:Q", bin=alt.Bin(step=1), title="Grade"),
            alt.Tooltip("count():Q", title="Students"),
            alt.Tooltip("subject:N", title="Subject")
        ]
    ).properties(
        width=600,
        height=350,
        title=f"Distribution of final grades — {subject_label} ({len(filtered_df)} students)"
    )
    return (chart,)


@app.cell
def _(chart, famsize, mo, school, sex, subject, test_panel, test_variable):
    ##Final Group 5 Dashboard Layout

    header = mo.md("""
    # Group 5 · Student Performance Dashboard

    **Members:** Anusha Ponna, Humphrey Chiranda, Muhammad Manzar Zamir
    """)

    # Filter section
    filter_panel = mo.vstack([
        mo.md("### Filters"),
        sex,
        school,
        famsize,
        mo.md("### Subject"),
            subject,
        mo.md("### Statistical comparison"),
        test_variable
    ], gap=1)

    # Chart section
    chart_panel = mo.vstack([
        mo.md("### Final Grade Distribution"),
        chart,
        mo.md("### Statistical results"),
        test_panel
    ], gap=2)

    # Combine filters and chart
    dashboard = mo.vstack([
        header,
        mo.hstack(
            [filter_panel, chart_panel],
            widths=[1, 3.5],
            gap=2,
            align="start")], gap=2)

    dashboard
    return


@app.cell
def _(mo):
    ###Create the statistical test selector

    test_variable = mo.ui.dropdown(
        options={
            "Sex": "sex",
            "School": "school",
            "Family size": "famsize",
        },
        value="Sex",
        label="Compare final grades by",
    )

    test_variable
    return (test_variable,)


@app.cell
def _(filtered_df, subject, test_variable):
    ###Summarise final grades for the selected comparison groups

    if subject.value == "both":
        comparison_summary = filtered_df.groupby(
            test_variable.value
        ).agg(
            Students=("G3_mat", "count"),
            Math_mean=("G3_mat", "mean"),
            Portuguese_mean=("G3_por", "mean")
        ).round(2)

    else:
        comparison_summary = filtered_df.groupby(
            test_variable.value
        ).agg(
            Students=("G3", "count"),
            Mean_grade=("G3", "mean")
        ).round(2)

    comparison_summary
    return


@app.cell
def _(filtered_df, pg, subject, test_variable):
    ###Check normality within each comparison group

    _grade_cols = (
        ["G3_mat", "G3_por"]
        if subject.value == "both"
        else ["G3"]
    )

    normality_results = {
        _col: pg.normality(
            data=filtered_df,
            dv=_col,
            group=test_variable.value
        )
        for _col in _grade_cols
    }

    normality_results
    return


@app.cell
def _(filtered_df, pg, subject, test_variable):
    ###Select and run the appropriate group comparison

    test_results = {}
    test_methods = {}

    _columns = (
        ["G3_mat", "G3_por"]
        if subject.value == "both"
        else ["G3"]
    )

    for _column in _columns:
        _groups = [
            _data[_column].dropna()
            for _, _data in filtered_df.groupby(test_variable.value)
        ]

        if len(_groups) != 2:
            test_results[_column] = "Select both groups for comparison."
            continue

        if min(map(len, _groups)) < 3:
            test_results[_column] = "At least 3 students per group are needed."
            continue

        if all(_g.var() == 0 for _g in _groups):
            test_results[_column] = "No within-group variation; test unavailable."
            continue

        _large = min(map(len, _groups)) >= 30
        _normal = all(
            _g.nunique() > 1
            and bool(pg.normality(_g)["normal"].iloc[0])
            for _g in _groups
        )

        if _large or _normal:
            test_methods[_column] = "Welch"
            test_results[_column] = pg.ttest(
                *_groups, paired=False, correction=True
            )
        else:
            test_methods[_column] = "Mann–Whitney"
            test_results[_column] = pg.mwu(
                *_groups, alternative="two-sided"
            )

    test_results
    return test_methods, test_results


@app.cell
def _(
    filtered_df,
    mo,
    subject_label,
    test_methods,
    test_results,
    test_variable,
):
    ###Explain the selected tests and their results

    _messages = []

    for _column, _result in test_results.items():
        _name = {
            "G3_mat": "Math",
            "G3_por": "Portuguese"
        }.get(_column, subject_label)

        if isinstance(_result, str):
            _messages.append(mo.callout(f"{_name}: {_result}", kind="warn"))
            continue

        _summary = filtered_df.groupby(test_variable.value)[_column].agg(
            ["count", "mean"]
        )
        _method = test_methods[_column]
        _p_col = "p_val" if "p_val" in _result.columns else "p-val"
        _p = float(_result[_p_col].iloc[0])

        _details = "; ".join(
            f"{_group}: mean {_row['mean']:.2f}/20 "
            f"(n = {int(_row['count'])})"
            for _group, _row in _summary.iterrows()
        )

        if _method == "Welch":
            _target = "mean grades"
            _reason = (
                "Both groups have at least 30 students."
                if _summary["count"].min() >= 30
                else "Neither group showed clear evidence against normality."
            )
            _reason += " Welch’s t-test allows unequal variances."
        else:
            _target = "grade ranks"
            _reason = (
                "At least one group is small and normality was not supported. "
                "Mann–Whitney compares ranks, not means."
            )

        _finding = (
            "a statistically significant difference"
            if _p < 0.05
            else "insufficient evidence of a difference"
        )

        _messages.append(mo.md(
            f"**{_name} — {_method} test:** {_details}. "
            f"We found {_finding} in {_target} "
            f"(p = {_p:.4f}; 5% significance level). "
            f"**Why this test?** {_reason}"
        ))

    test_panel = mo.vstack(_messages)
    test_panel
    return (test_panel,)


if __name__ == "__main__":
    app.run()
