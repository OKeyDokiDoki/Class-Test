# -*- coding: utf-8 -*-
"""从 db_model.py 生成后端持久化代码：JPA 实体、Repository、建表引导与写入校验程序。

所属链路
    db_model.py  --本脚本-->  backend/src/main/java/com/lifecircle/{domain,repository,config,service}
    （物理表由 dbdiagram.io 导出的 DDL 创建，见 backend/src/main/resources/db/schema-dbml-oracle.sql）

生成的代码
    domain/*.java                        27 个 JPA 实体，字段与物理表列名一一对应
                                         - @Table/@Column 使用 snake_case 列名
                                         - 主键 GenerationType.IDENTITY
                                         - @DynamicInsert/@DynamicUpdate，让数据库默认值生效
                                         - @PrePersist 兜底 created_at/updated_at
    repository/*Repository.java          27 个 Spring Data JPA 仓储
    config/SchemaBootstrapRunner.java    H2 回退：首次启动执行 schema-dbml-h2.sql
    config/OracleSchemaBootstrapRunner.java  Oracle：首次启动执行 schema-dbml-oracle.sql
    service/PersistenceDemoRunner.java   演示写入 + 输出各表行数（--persistence.exit-after-demo=true 用完即退）
    resources/application-h2file.yml     H2 文件库 profile

不会生成（人工维护）
    application.yml / application-oracle.yml / application-h2.yml / 测试用 application.yml
    以及业务 Service、Controller

依赖
    纯标准库（生成 Java 源码，不需要额外 pip 包）

运行
    cd tools/db-toolchain
    python gen_backend_persistence.py

注意
    本脚本会覆盖上面列出的 Java 文件，请勿手工修改这些生成文件；
    要改映射规则请改 db_model.py 或本脚本的模板函数。
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db_model as M

# --- 路径约定 ---------------------------------------------------------------
# 本文件位于 <repo>/tools/db-toolchain/，向上两级就是仓库根目录。
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("DB_REPO_ROOT") or os.path.dirname(os.path.dirname(HERE))
BACKEND = os.path.join(REPO, "backend")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "lifecircle")
RES = os.path.join(BACKEND, "src", "main", "resources")
DOMAIN = os.path.join(JAVA, "domain")
REPO_DIR = os.path.join(JAVA, "repository")
CONFIG = os.path.join(JAVA, "config")
SERVICE = os.path.join(JAVA, "service")

for d in (DOMAIN, REPO_DIR, CONFIG, SERVICE, os.path.join(RES, "db")):
    os.makedirs(d, exist_ok=True)

TABLES = M.TABLES
BY = M.TABLE_BY_NAME


# --------------------------------------------------------------------------
# naming and type conversion
# --------------------------------------------------------------------------
def camel(name):
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def pascal(name):
    return "".join(p.capitalize() for p in name.split("_"))


def type_parts(typ):
    m = re.match(r"([A-Z]+)(?:\(([^)]*)\))?$", typ)
    return m.group(1), (m.group(2) or "")


def java_type(typ):
    base, args = type_parts(typ)
    return {"BIGINT": "Long", "INT": "Integer", "VARCHAR": "String", "CHAR": "String",
            "DECIMAL": "BigDecimal", "DATE": "LocalDate", "TIMESTAMP": "Instant",
            "CLOB": "String"}[base]


def column_attrs(c):
    base, args = type_parts(c["typ"])
    attrs = [f'name = "{c["name"]}"']
    if base in ("VARCHAR", "CHAR") and args:
        attrs.append(f"length = {args}")
    if base == "DECIMAL" and args:
        p, s = args.split(",")
        attrs.append(f"precision = {p}")
        attrs.append(f"scale = {s}")
    if not c["null"]:
        attrs.append("nullable = false")
    return ", ".join(attrs)


IMPORTS = {
    "BigDecimal": "java.math.BigDecimal",
    "LocalDate": "java.time.LocalDate",
    "Instant": "java.time.Instant",
}


def needs_import(jtype):
    return IMPORTS.get(jtype)


# --------------------------------------------------------------------------
# entities
# --------------------------------------------------------------------------
def gen_entity(t):
    cls = pascal(t["name"])
    fields = []
    body_getset = []
    used_imports = set()
    has_created = any(c["name"] == "createdAt" and c["name"] == "createdAt" for c in t["cols"])
    field_names = {c["name"] for c in t["cols"]}
    lines = []
    lines.append("package com.lifecircle.domain;")
    lines.append("")
    lines.append("import jakarta.persistence.Column;")
    lines.append("import jakarta.persistence.Entity;")
    lines.append("import jakarta.persistence.GeneratedValue;")
    lines.append("import jakarta.persistence.GenerationType;")
    lines.append("import jakarta.persistence.Id;")
    lines.append("import jakarta.persistence.PrePersist;")
    lines.append("import jakarta.persistence.Table;")
    lines.append("import org.hibernate.annotations.DynamicInsert;")
    lines.append("import org.hibernate.annotations.DynamicUpdate;")
    lines.append("")
    simple_imports = []
    for c in t["cols"]:
        jt = java_type(c["typ"])
        if jt in IMPORTS:
            simple_imports.append(IMPORTS[jt])
    for imp in sorted(set(simple_imports)):
        lines.append(f"import {imp};")
    if simple_imports:
        lines.append("")
    lines.append("@Entity")
    lines.append("@DynamicInsert")
    lines.append("@DynamicUpdate")
    lines.append(f'@Table(name = "{t["name"]}")')
    lines.append(f"public class {cls} {{")
    lines.append("")
    for c in t["cols"]:
        jt = java_type(c["typ"])
        fname = camel(c["name"])
        if c["pk"]:
            lines.append("    @Id")
            lines.append("    @GeneratedValue(strategy = GenerationType.IDENTITY)")
        lines.append(f'    @Column({column_attrs(c)})')
        lines.append(f"    private {jt} {fname};")
        lines.append("")
        body_getset.append(f"    public {jt} get{pascal(c['name'])}() {{")
        body_getset.append(f"        return {fname};")
        body_getset.append("    }")
        body_getset.append("")
        body_getset.append(f"    public void set{pascal(c['name'])}({jt} {fname}) {{")
        body_getset.append(f"        this.{fname} = {fname};")
        body_getset.append("    }")
        body_getset.append("")
    lines.append(f"    public {cls}() {{")
    lines.append("    }")
    lines.append("")
    lines.extend(body_getset)
    if "created_at" in field_names or "updated_at" in field_names:
        lines.append("    @PrePersist")
        lines.append("    void prePersist() {")
        if "created_at" in field_names:
            lines.append("        if (createdAt == null) {")
            lines.append("            createdAt = Instant.now();")
            lines.append("        }")
        if "updated_at" in field_names:
            lines.append("        if (updatedAt == null) {")
            lines.append("            updatedAt = Instant.now();")
            lines.append("        }")
        lines.append("    }")
        lines.append("")
    lines.append("}")
    return "\n".join(lines) + "\n"


def gen_repo(t):
    cls = pascal(t["name"])
    return f"""package com.lifecircle.repository;

import com.lifecircle.domain.{cls};
import org.springframework.data.jpa.repository.JpaRepository;

public interface {cls}Repository extends JpaRepository<{cls}, Long> {{
}}
"""


# --------------------------------------------------------------------------
# topological order
# --------------------------------------------------------------------------
order = []
seen = set()
visiting = set()


def visit(t):
    if t["name"] in seen:
        return
    if t["name"] in visiting:
        raise SystemExit("cycle at " + t["name"])
    visiting.add(t["name"])
    for c in t["cols"]:
        if c["fk"]:
            dep = c["fk"].split(".")[0]
            if dep != t["name"]:
                visit(BY[dep])
    visiting.discard(t["name"])
    seen.add(t["name"])
    order.append(t)


for t in TABLES:
    visit(t)

VAR = {t["name"]: camel(t["name"]) for t in TABLES}
IDVAR = {t["name"]: camel(t["name"]) + "Id" for t in TABLES}


def sample_value(t, c, suffix):
    name, jt = c["name"], java_type(c["typ"])
    if c["fk"]:
        parent = c["fk"].split(".")[0]
        if parent == t["name"]:
            return None
        return IDVAR[parent]
    if jt == "Long":
        return "1L"
    if jt == "Integer":
        if name.endswith("_score") or name.endswith("_pct") or name in ("coverage", "total_score"):
            return "80"
        if name in ("before_coverage", "after_coverage"):
            return "80"
        return "1"
    if jt == "BigDecimal":
        if name in ("lng", "center_lng"):
            return 'new BigDecimal("104.043100")'
        if name in ("lat", "center_lat"):
            return 'new BigDecimal("30.642100")'
        if "score" in name or "weight" in name or "pct" in name or "coverage" in name:
            return 'new BigDecimal("80")'
        return 'new BigDecimal("1")'
    if jt == "LocalDate":
        return "LocalDate.now()"
    if jt == "Instant":
        return "Instant.now()"
    if jt == "String":
        special = {
            "role_code": '"RESIDENT"', "profile_type": '"RESIDENT"',
            "profile_label": '"青年通勤型"', "dimension_code": '"FRESH"',
            "dimension_name": '"生鲜购物"', "tag_code": 'unique("TAG")',
            "category_code": 'unique("CAT")', "district_code": 'unique("DIST")',
            "grid_code": 'unique("GRID")', "node_code": 'unique("NODE")',
            "segment_code": 'unique("SEG")', "batch_no": 'unique("BATCH")',
            "source_poi_id": 'unique("SRC")', "resident_code": 'unique("RES")',
            "user_code": 'unique("USER")', "source": '"MANUAL"',
            "data_source": '"AMAP"', "sync_type": '"INCREMENT"',
            "change_type": '"INSERT"', "severity": '"LOW"',
            "rule_code": '"DUP_POI"', "gap_level": '"高"',
            "issue": '"夜间就医距离较远"', "issue_desc": '"坐标越界"',
            "poi_name": 'unique("POI")', "candidate_name": '"东园路口"',
            "merchant_name": 'unique("商户")', "business_type": '"便利店"',
            "area_name": '"东南片区"', "contact": '"13800138000"',
            "category_name": '"菜市场"', "tag_name": '"生鲜买菜"',
    "insight": '"配套总体便利"', "pipeline": '"x"',
        }
        if name in special:
            return special[name]
        if c["uniq"]:
            return f'unique("{c["name"][:4].upper()}")'
        return f'"V" + suffix'
    return "null"


def gen_runner():
    lines = []
    lines.append("package com.lifecircle.service;")
    lines.append("")
    lines.append("import com.lifecircle.domain.*;")
    lines.append("import com.lifecircle.repository.*;")
    lines.append("import org.springframework.beans.factory.annotation.Value;")
    lines.append("import org.springframework.boot.CommandLineRunner;")
    lines.append("import org.springframework.context.annotation.Profile;")
    lines.append("import org.springframework.core.annotation.Order;")
    lines.append("import org.springframework.stereotype.Component;")
    lines.append("")
    lines.append("import java.math.BigDecimal;")
    lines.append("import java.time.Instant;")
    lines.append("import java.time.LocalDate;")
    lines.append("")
    lines.append("/**")
    lines.append(" * 持久化演示：向物理数据库中写入一行数据，并输出各表行数。")
    lines.append(" * 第二次启动时数据仍然存在，用于验证文件数据库的真实持久化。")
    lines.append(" */")
    lines.append("@Component")
    lines.append('@Profile("demo")')
    lines.append("@Order(10)")
    lines.append("public class PersistenceDemoRunner implements CommandLineRunner {")
    lines.append("    private final String suffix = String.valueOf(System.currentTimeMillis() % 100000L);")
    lines.append("")
    lines.append('    @Value("${persistence.exit-after-demo:false}")')
    lines.append("    private boolean exitAfterDemo;")
    lines.append("")
    for t in TABLES:
        cls = pascal(t["name"])
        lines.append(f"    private final {cls}Repository {VAR[t['name']]}Repository;")
    lines.append("")
    lines.append("    public PersistenceDemoRunner(")
    params = [f"{pascal(t['name'])}Repository {VAR[t['name']]}Repository" for t in TABLES]
    for i, p in enumerate(params):
        tail = "," if i < len(params) - 1 else ") {"
        lines.append(f"            {p}{tail}")
    for t in TABLES:
        v = VAR[t["name"]]
        lines.append(f"        this.{v}Repository = {v}Repository;")
    lines.append("    }")
    lines.append("")
    lines.append("    @Override")
    lines.append("    public void run(String... args) {")
    lines.append("        boolean empty = districtRepository.count() == 0;")
    lines.append("        if (empty) {")
    lines.append("            seed();")
    lines.append('            System.out.println("[demo] 首次启动：已向物理数据库写入演示数据");')
    lines.append("        } else {")
    lines.append('            System.out.println("[demo] 再次启动：数据库中已有数据，跳过写入");')
    lines.append("        }")
    lines.append("        summary();")
    lines.append("        if (exitAfterDemo) {")
    lines.append("            System.exit(0);")
    lines.append("        }")
    lines.append("    }")
    lines.append("")
    lines.append("    private static String unique(String prefix) {")
    lines.append("        return prefix + System.currentTimeMillis() % 1000000L;")
    lines.append("    }")
    lines.append("")
    lines.append("    private void seed() {")
    for t in order:
        cls = pascal(t["name"])
        v = VAR[t["name"]]
        lines.append(f"        {cls} {v} = new {cls}();")
        for c in t["cols"]:
            if c["pk"]:
                continue
            # DBML 未导出 CURRENT_TIMESTAMP 默认值，因此这类列必须由代码赋值
            required = (not c["null"]) and (c["default"] is None or c["default"] == "CURRENT_TIMESTAMP")
            if not required:
                continue
            val = sample_value(t, c, "suffix")
            if val is None:
                continue
            if val == "unique(...)":
                continue
            lines.append(f"        {v}.set{pascal(c['name'])}({val});")
        # fill unique fields even when nullable
        for c in t["cols"]:
            if c["pk"] or not c["uniq"]:
                continue
            if (not c["null"]) and not c["default"]:
                continue
            val = sample_value(t, c, "suffix")
            if val is None or val == "null":
                val = f'unique("{c["name"][:4].upper()}")'
            lines.append(f"        {v}.set{pascal(c['name'])}({val});")
        lines.append(f"        {v} = {v}Repository.save({v});")
        lines.append(f"        Long {IDVAR[t['name']]} = {v}.getId();")
        lines.append("")
    lines.append("    }")
    lines.append("")
    lines.append("    private void summary() {")
    lines.append('        System.out.println("[demo] 物理数据库各表行数：");')
    for t in TABLES:
        v = VAR[t["name"]]
        lines.append(f'        System.out.println("  {t["name"]} = " + {v}Repository.count());')
    lines.append("    }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def gen_bootstrap():
    return """package com.lifecircle.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.core.annotation.Order;
import org.springframework.core.io.Resource;
import org.springframework.jdbc.datasource.init.ScriptUtils;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

/**
 * 首次启动时执行 dbdiagram.io DBML 导出的建表脚本。
 * 表已存在则跳过，保证物理库只在第一次创建。
 */
@Component
@Profile({"h2file", "h2"})
@Order(1)
public class SchemaBootstrapRunner implements CommandLineRunner {
    private final DataSource dataSource;
    private final Resource schemaScript;

    public SchemaBootstrapRunner(DataSource dataSource,
            @Value("${persistence.schema-script:classpath:db/schema-dbml-h2.sql}") Resource schemaScript) {
        this.dataSource = dataSource;
        this.schemaScript = schemaScript;
    }

    @Override
    public void run(String... args) throws Exception {
        try (Connection connection = dataSource.getConnection()) {
            if (tableExists(connection)) {
                System.out.println("[schema] 物理表已存在，跳过建表");
                return;
            }
            ScriptUtils.executeSqlScript(connection, schemaScript);
            System.out.println("[schema] 已按 dbdiagram.io DBML 导出脚本创建物理表");
        }
    }

    private boolean tableExists(Connection connection) throws Exception {
        try (Statement st = connection.createStatement();
             ResultSet rs = st.executeQuery(
                 "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                 + "WHERE TABLE_SCHEMA='PUBLIC' AND TABLE_NAME='app_user'")) {
            rs.next();
            return rs.getInt(1) > 0;
        }
    }
}
"""


def gen_oracle_bootstrap():
    return """package com.lifecircle.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.core.annotation.Order;
import org.springframework.core.io.Resource;
import org.springframework.jdbc.datasource.init.ScriptUtils;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

/**
 * Oracle 首次启动时执行 dbdiagram.io DBML 导出的 Oracle 建表脚本。
 * 表已存在则跳过，避免覆盖已有数据。
 * 由 app.datasource.mode=oracle（默认）控制是否生效，不依赖 profile 名称。
 */
@Component
@ConditionalOnProperty(prefix = "app.datasource", name = "mode", havingValue = "oracle", matchIfMissing = true)
@Order(1)
public class OracleSchemaBootstrapRunner implements CommandLineRunner {
    private final DataSource dataSource;
    private final Resource schemaScript;

    public OracleSchemaBootstrapRunner(DataSource dataSource,
            @Value("${persistence.schema-script:classpath:db/schema-dbml-oracle.sql}") Resource schemaScript) {
        this.dataSource = dataSource;
        this.schemaScript = schemaScript;
    }

    @Override
    public void run(String... args) throws Exception {
        try (Connection connection = dataSource.getConnection()) {
            if (tableExists(connection)) {
                System.out.println("[schema] Oracle 物理表已存在，跳过建表");
                return;
            }
            ScriptUtils.executeSqlScript(connection, schemaScript);
            System.out.println("[schema] 已按 dbdiagram.io DBML 导出脚本在 Oracle 创建物理表");
        }
    }

    private boolean tableExists(Connection connection) throws Exception {
        try (Statement st = connection.createStatement();
             ResultSet rs = st.executeQuery(
                 "SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = 'app_user'")) {
            rs.next();
            return rs.getInt(1) > 0;
        }
    }
}
"""


def main():
    for t in TABLES:
        open(os.path.join(DOMAIN, pascal(t["name"]) + ".java"), "w", encoding="utf-8").write(gen_entity(t))
        open(os.path.join(REPO_DIR, pascal(t["name"]) + "Repository.java"), "w", encoding="utf-8").write(gen_repo(t))
    open(os.path.join(SERVICE, "PersistenceDemoRunner.java"), "w", encoding="utf-8").write(gen_runner())
    open(os.path.join(CONFIG, "SchemaBootstrapRunner.java"), "w", encoding="utf-8").write(gen_bootstrap())
    open(os.path.join(CONFIG, "OracleSchemaBootstrapRunner.java"), "w", encoding="utf-8").write(gen_oracle_bootstrap())
    yml = """# H2 文件库：无 Oracle 环境时的持久化回退，数据落在 backend/data/lifecircle.mv.db
app:
  datasource:
    mode: h2

spring:
  datasource:
    url: jdbc:h2:file:./data/lifecircle;MODE=PostgreSQL;DB_CLOSE_ON_EXIT=FALSE
    username: sa
    password:
    driver-class-name: org.h2.Driver
  jpa:
    database-platform: org.hibernate.dialect.H2Dialect
    open-in-view: false
    hibernate:
      # 物理表由 dbdiagram.io 导出的脚本创建，禁止 Hibernate 自动建表
      ddl-auto: none
    properties:
      hibernate:
        globally_quoted_identifiers: true
  h2:
    console:
      enabled: true

persistence:
  schema-script: classpath:db/schema-dbml-h2.sql
"""
    open(os.path.join(RES, "application-h2file.yml"), "w", encoding="utf-8").write(yml)
    print("entities", len(TABLES), "repositories", len(TABLES))


if __name__ == "__main__":
    main()