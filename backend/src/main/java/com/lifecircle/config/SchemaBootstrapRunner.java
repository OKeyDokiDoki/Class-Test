package com.lifecircle.config;

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
@Profile("h2file")
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
