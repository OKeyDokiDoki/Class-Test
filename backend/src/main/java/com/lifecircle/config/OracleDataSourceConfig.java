package com.lifecircle.config;

import com.zaxxer.hikari.HikariDataSource;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.jdbc.datasource.LazyConnectionDataSourceProxy;

import javax.sql.DataSource;
import java.util.Map;

/**
 * Oracle 读写分离数据源。
 *
 * 由配置项 app.datasource.mode 控制是否生效（默认 oracle）：
 *   oracle  -> 使用主库/只读库路由数据源（当前配置）
 *   h2/h2file -> 不生效，改用 profile 里的 H2 数据源
 * 这样不依赖 profile 名称，-Dspring-boot.run.profiles=demo 之类的组合不会误连 Oracle。
 */
@Configuration
@ConditionalOnProperty(prefix = "app.datasource", name = "mode", havingValue = "oracle", matchIfMissing = true)
public class OracleDataSourceConfig {
    @Bean
    @ConfigurationProperties("app.datasource.master")
    public DataSourceProperties masterDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    @ConfigurationProperties("app.datasource.replica")
    public DataSourceProperties replicaDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    public DataSource masterDataSource(
        @Qualifier("masterDataSourceProperties") DataSourceProperties properties
    ) {
        return properties.initializeDataSourceBuilder()
            .type(HikariDataSource.class)
            .build();
    }

    @Bean
    public DataSource replicaDataSource(
        @Qualifier("replicaDataSourceProperties") DataSourceProperties properties
    ) {
        return properties.initializeDataSourceBuilder()
            .type(HikariDataSource.class)
            .build();
    }

    @Bean
    @Primary
    public DataSource dataSource(
        @Qualifier("masterDataSource") DataSource master,
        @Qualifier("replicaDataSource") DataSource replica
    ) {
        ReadWriteRoutingDataSource routingDataSource = new ReadWriteRoutingDataSource();
        routingDataSource.setDefaultTargetDataSource(master);
        routingDataSource.setTargetDataSources(Map.of(
            DataSourceType.MASTER, master,
            DataSourceType.REPLICA, replica
        ));
        routingDataSource.afterPropertiesSet();

        // 延迟获取连接，确保 @Transactional(readOnly = true) 已经生效后再选库。
        return new LazyConnectionDataSourceProxy(routingDataSource);
    }
}
